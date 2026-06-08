# main.py
import sys
from PyQt6.QtWidgets import QApplication, QDialog, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QMessageBox, QSplitter
from PyQt6.QtCore import Qt
from camera_dialog import CameraDialog  # Изменен импорт
from widgets.datetime_widget import DateTimeWidget
from widgets.header_widget import HeaderWidget
from widgets.table_widget import InfoTableWidget
from widgets.video_widget import VideoWidget
from widgets.effects_widget import EffectsWidget 
class MainWindow(QWidget):
    def __init__(self):
        super().__init__()
        self.video_widget = None
        self.initUI()
    
    def initUI(self):
        self.setWindowTitle("Мультимедийное приложение")
        self.setGeometry(100, 100, 1000, 600)  # Увеличил ширину для виджета эффектов
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
        # Создаём горизонтальный layout для левой панели (дата/время + эффекты) и видео
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        # Создаём горизонтальный layout для виджета эффектов и видео
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        # Добавляем виджет даты и времени сверху
        self.datetime_widget = DateTimeWidget()
        left_layout.addWidget(self.datetime_widget)
        # Добавляем виджет эффектов слева
        self.effects_widget = EffectsWidget()
        self.effects_widget.effect_applied.connect(self.on_effect_applied)
        self.effects_widget.effect_reset.connect(self.on_effect_reset)
        left_layout.addWidget(self.effects_widget)
        
        content_layout.addWidget(left_panel)
        
        # Создаём правую часть (видео + информация)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
         # Создаём виджет для видео
        self.video_widget = VideoWidget()
        # Подключаем сигнал обнаружения людей
        self.video_widget.person_detected_signal.connect(self.on_person_detected)
        right_layout.addWidget(self.video_widget)
        # Виджет таблицы 
        self.info_table = InfoTableWidget()
        self.info_table.setMaximumHeight(200) # высота
        self.info_table.row_selected.connect(self.on_table_row_selected)
        right_layout.addWidget(self.info_table)
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
        right_layout.addWidget(info_widget)
        
        content_layout.addWidget(right_widget)  # Добавляем правую часть
        main_layout.addLayout(content_layout)   # Добавляем горизонтальный layout
        
        self.setLayout(main_layout)
        self.apply_styles()
    # Добавьте новый метод для обработки обнаружения людей:
    def on_person_detected(self, count, positions):
        """Обработчик обнаружения людей"""
        # Формируем детальное сообщение
        if count == 1:
            action_name = "Обнаружен человек"
        else:
            action_name = f"Обнаружено {count} человек"
        
        # Детали с позициями
        if positions and len(positions) > 0:
            # Преобразуем позиции в читаемый формат
            pos_list = []
            for i, pos in enumerate(positions):
                if isinstance(pos, tuple):
                    pos_list.append(f"#{i+1}: {pos}")
                else:
                    pos_list.append(pos)
            details = f"{count} чел. Позиции: {', '.join(pos_list)}"
        else:
            details = f"Найдено {count} человек в кадре"
        
        # Добавляем запись в таблицу
        self.info_table.add_row("Детекция", action_name, details)
        
        # Обновляем строку состояния
        self.last_action_label.setText(f"Последнее действие: {action_name}")    
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
        # Определяем тип файла по расширению
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        
        file_ext = file_path.lower()
        is_image = any(file_ext.endswith(ext) for ext in image_extensions)
        is_video = any(file_ext.endswith(ext) for ext in video_extensions)
        
        if is_image:
            action_name = "Открыто изображение"
            details = f"Файл: {file_path.split('/')[-1]}"
            self.info_table.add_row("Файл", action_name, details)
            self.last_action_label.setText(f"Последнее действие: {action_name} → {file_path.split('/')[-1]}")
            
            # Загружаем изображение
            self.video_widget.load_image(file_path)
            
        elif is_video:
            # Существующий код для видео
            QMessageBox.information(
                self,
                "Файл открыт",
                f"Вы открыли файл:\n{file_path}"
            )
            self.last_action_label.setText(f"Последнее действие: Открыт файл → {file_path}")
            
            self.video_widget.video_label.setStyleSheet("""
                QLabel {
                    background-color: black;
                    border: 2px solid #333;
                    border-radius: 5px;
                    min-height: 400px;
                }
            """)
            
            self.video_widget.load_video(file_path)
            
        else:
            QMessageBox.warning(
                self,
                "Неподдерживаемый формат",
                f"Файл {file_path} имеет неподдерживаемый формат.\n\n"
                f"Поддерживаемые форматы:\n"
                f"Видео: {', '.join(video_extensions)}\n"
                f"Изображения: {', '.join(image_extensions)}"
            )
    
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
    def on_effect_applied(self, effect_name, params):
        """Применяет выбранный эффект к видео"""
        if self.video_widget:
            if effect_name == "detect_person":
                # Включение/выключение детектора людей
                enabled = params.get("enabled", False)
                threshold = params.get("threshold", 0.5)
                self.video_widget.enable_person_detection(enabled, threshold)
                
                if enabled:
                    self.info_table.add_row("Детекция", "Поиск людей включён", f"Порог: {threshold}")
                    self.last_action_label.setText(f"Последнее действие: Включён поиск людей (порог {threshold})")
                else:
                    self.info_table.add_row("Детекция", "Поиск людей выключен", "")
                    self.last_action_label.setText("Последнее действие: Выключен поиск людей")
            else:
                self.video_widget.apply_effect(effect_name, params)
                self.last_action_label.setText(f"Последнее действие: Применён эффект '{effect_name}'")

    def on_effect_reset(self):
        """Сбрасывает эффекты"""
        if self.video_widget:
            self.video_widget.reset_effects()
            self.last_action_label.setText("Последнее действие: Эффекты сброшены")
    def on_table_row_selected(self, row, data):
        """Обработчик выбора строки в таблице"""
        # Можно добавить дополнительную логику при выборе строки
        print(f"Выбрана строка {row}: {data}")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())