# main.py
import sys
from PyQt6.QtWidgets import QApplication, QDialog, QWidget, QVBoxLayout, QLabel, QMessageBox, QSplitter
from PyQt6.QtCore import Qt
from camera_dialog import CameraDialog  # Изменен импорт
from widgets.header_widget import HeaderWidget
from widgets.video_widget import VideoWidget

class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.video_widget = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Мультимедийное приложение")
        self.setGeometry(100, 100, 800, 600)
        self.setContentsMargins(0, 0, 0, 0)
        
        main_layout = QVBoxLayout()
        main_layout.setContentsMargins(0, 0, 0, 0)
        main_layout.setSpacing(0)
        
        # Добавляем шапку с кнопками
        self.header = HeaderWidget()
        
        # Подключаем сигналы от шапки
        self.header.button1_clicked.connect(self.on_button1_clicked)
        self.header.button2_clicked.connect(self.on_button2_clicked)
        self.header.button3_clicked.connect(self.on_button3_clicked)
        self.header.button4_clicked.connect(self.on_button4_clicked)
        self.header.clear_clicked.connect(self.on_clear_clicked)
        self.header.file_opened.connect(self.on_file_opened)
        
        main_layout.addWidget(self.header)
        
        # Создаём разделитель для видео и информационной панели
        self.content_splitter = QSplitter(Qt.Orientation.Vertical)
        
        # Создаём виджет для видео (всегда видим)
        self.video_widget = VideoWidget()
        self.content_splitter.addWidget(self.video_widget)
        
        # Информационная панель внизу
        info_widget = QWidget()
        info_layout = QVBoxLayout(info_widget)
        
        self.last_action_label = QLabel("Последнее действие: -")
        self.last_action_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.last_action_label.setStyleSheet("""
            QLabel {
                font-size: 14px;
                padding: 10px;
                color: #666;
                background-color: #f5f5f5;
                border-top: 1px solid #ddd;
            }
        """)
        
        info_layout.addWidget(self.last_action_label)
        self.content_splitter.addWidget(info_widget)
        
        # Устанавливаем начальные размеры (видео занимает 70%, информационная панель 30%)
        self.content_splitter.setSizes([400, 200])
        
        main_layout.addWidget(self.content_splitter)
        self.setLayout(main_layout)
        self.apply_styles()
        
    def apply_styles(self):
        self.setStyleSheet("""
            QWidget {
                background-color: white;
            }
            QSplitter::handle {
                background-color: #ddd;
            }
            QSplitter::handle:vertical {
                height: 2px;
            }
        """)
    
    def on_button1_clicked(self, item):
        self.last_action_label.setText(f"Последнее действие: Файл → {item}")
        if item == "Открыть файл...":
            pass  # Сигнал уже обрабатывается в header_widget
        elif item == "Камера":
            self.start_camera()  # Вызываем start_camera, а не show_camera_selection_dialog
    
    def on_button2_clicked(self, item):
        self.last_action_label.setText(f"Последнее действие: Правка → {item}")
        # Здесь можно добавить обработку команд редактирования
        
    def on_button3_clicked(self, item):
        self.last_action_label.setText(f"Последнее действие: Вид → {item}")
        # Обработка команд вида
        if item == "На весь экран":
            self.toggle_fullscreen()
    
    def on_button4_clicked(self, item):
        self.last_action_label.setText(f"Последнее действие: Справка → {item}")
        if item == "О программе":
            QMessageBox.about(self, "О программе",
                            "<h3>Мультимедийное приложение</h3>"
                            "<p>Версия 1.0</p>"
                            "<p>Приложение для воспроизведения и обработки видео</p>"
                            "<p>Использует Qt6 и OpenCV</p>")
    
    def on_clear_clicked(self):
        self.last_action_label.setText("Последнее действие: -")
        # Очищаем видео, если оно загружено
        if self.video_widget.current_video_path or self.video_widget.is_camera_mode:
            reply = QMessageBox.question(self, "Очистить",
                                       "Вы действительно хотите остановить текущее воспроизведение?",
                                       QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No)
            if reply == QMessageBox.StandardButton.Yes:
                if self.video_widget.is_camera_mode:
                    self.video_widget.stop_camera()
                else:
                    self.video_widget.stop_video()
                self.video_widget.current_video_path = None
    
    def on_file_opened(self, file_path):
        """Обработчик открытия файла"""
        # Показываем информационное сообщение
        QMessageBox.information(
            self,
            "Файл открыт",
            f"Вы открыли файл:\n{file_path}"
        )
        self.last_action_label.setText(f"Последнее действие: Открыт файл → {file_path}")
        
        # Восстанавливаем нормальный стиль QLabel
        self.video_widget.video_label.setStyleSheet("""
            QLabel {
                background-color: black;
                border: 2px solid #333;
                border-radius: 5px;
                min-height: 400px;
            }
        """)
        
        # Загружаем видео
        self.video_widget.load_video(file_path)
    
    def start_camera(self):
        """Запускает диалог выбора камеры"""
        dialog = CameraDialog(self)  # Используем CameraDialog, а не CameraSelectionDialog
        if dialog.exec() == QDialog.DialogCode.Accepted:
            camera_id = dialog.get_selected_camera()
            if camera_id is not None:
                self.last_action_label.setText(f"Последнее действие: Запуск камеры (ID: {camera_id})")
                
                # Восстанавливаем нормальный стиль QLabel
                self.video_widget.video_label.setStyleSheet("""
                    QLabel {
                        background-color: black;
                        border: 2px solid #333;
                        border-radius: 5px;
                        min-height: 400px;
                    }
                """)
                
                # Запускаем выбранную камеру
                self.video_widget.switch_to_camera_mode(camera_id=camera_id)
    
    def toggle_fullscreen(self):
        """Переключает полноэкранный режим"""
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())