import sys
from PyQt6.QtWidgets import QApplication, QDialog, QHBoxLayout, QWidget, QVBoxLayout, QLabel, QMessageBox, QSplitter
from PyQt6.QtCore import Qt
from camera_dialog import CameraDialog
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
        self.setGeometry(100, 100, 1000, 600)
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
        
        # Создаём горизонтальный layout для левой панели и видео
        content_layout = QHBoxLayout()
        content_layout.setContentsMargins(0, 0, 0, 0)
        content_layout.setSpacing(0)
        
        # Левая панель
        left_panel = QWidget()
        left_panel.setFixedWidth(250)
        left_layout = QVBoxLayout(left_panel)
        left_layout.setContentsMargins(0, 0, 0, 0)
        left_layout.setSpacing(0)
        
        # Виджет даты и времени
        self.datetime_widget = DateTimeWidget()
        left_layout.addWidget(self.datetime_widget)
        
        # Виджет эффектов
        self.effects_widget = EffectsWidget()
        self.effects_widget.effect_applied.connect(self.on_effect_applied)
        self.effects_widget.effect_reset.connect(self.on_effect_reset)
        left_layout.addWidget(self.effects_widget)
        
        content_layout.addWidget(left_panel)
        
        # Правая часть (видео + таблица)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)
        right_layout.setContentsMargins(0, 0, 0, 0)
        right_layout.setSpacing(0)
        
        # Виджет видео
        self.video_widget = VideoWidget()
        self.video_widget.person_detected_signal.connect(self.on_person_detected)
        self.video_widget.shelves_detected_signal.connect(self.on_shelves_detected)
        self.video_widget.fire_detected_signal.connect(self.on_fire_detected)
        right_layout.addWidget(self.video_widget)
        
        # Виджет таблицы
        self.info_table = InfoTableWidget()
        self.info_table.row_selected.connect(self.on_table_row_selected)
        right_layout.addWidget(self.info_table)
        
        content_layout.addWidget(right_widget)
        main_layout.addLayout(content_layout)
        
        self.setLayout(main_layout)
        self.apply_styles()
    
    def on_person_detected(self, count, positions):
        """Обработчик обнаружения людей"""
        if count == 1:
            action_name = "Обнаружен человек"
        else:
            action_name = f"Обнаружено {count} человек"
        
        if positions and len(positions) > 0:
            pos_list = []
            for i, pos in enumerate(positions):
                if isinstance(pos, tuple):
                    pos_list.append(f"#{i+1}: {pos}")
                else:
                    pos_list.append(pos)
            details = f"{count} чел. Позиции: {', '.join(pos_list)}"
        else:
            details = f"Найдено {count} человек в кадре"
        
        self.info_table.add_row("Детекция", action_name, details)
    
    def on_shelves_detected(self, shelves, cells):
        """Обработчик обнаружения ячеек"""
        total_cells = len(cells)
        
        if total_cells > 0:
            action_name = f"Обнаружено {total_cells} ячеек"
            details = f"Найдено {total_cells} ячеек на изображении"
            self.info_table.add_row("Детекция", action_name, details)
    
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
        if item == "Открыть файл...":
            pass
        elif item == "Камера":
            self.start_camera()
    
    def on_button2_clicked(self, item):
        pass
        
    def on_button3_clicked(self, item):
        if item == "На весь экран":
            self.toggle_fullscreen()
    
    def on_button4_clicked(self, item):
        if item == "О программе":
            QMessageBox.about(self, "О программе",
                            "<h3>Мультимедийное приложение</h3>"
                            "<p>Версия 1.0</p>"
                            "<p>Приложение для воспроизведения и обработки видео</p>"
                            "<p>Использует Qt6 и OpenCV</p>")
    
    def on_clear_clicked(self):
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
        image_extensions = ['.jpg', '.jpeg', '.png', '.bmp', '.tiff', '.gif']
        video_extensions = ['.mp4', '.avi', '.mov', '.mkv', '.flv', '.wmv']
        
        file_ext = file_path.lower()
        is_image = any(file_ext.endswith(ext) for ext in image_extensions)
        is_video = any(file_ext.endswith(ext) for ext in video_extensions)
        
        if is_image:
            action_name = "Открыто изображение"
            details = f"Файл: {file_path.split('/')[-1]}"
            self.info_table.add_row("Файл", action_name, details)
            self.video_widget.load_image(file_path)
            
        elif is_video:
            QMessageBox.information(
                self,
                "Файл открыт",
                f"Вы открыли файл:\n{file_path}"
            )
            
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
        dialog = CameraDialog(self)
        if dialog.exec() == QDialog.DialogCode.Accepted:
            camera_id = dialog.get_selected_camera()
            if camera_id is not None:
                self.video_widget.video_label.setStyleSheet("""
                    QLabel {
                        background-color: black;
                        border: 2px solid #333;
                        border-radius: 5px;
                        min-height: 400px;
                    }
                """)
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
            if effect_name == "all":
                self.video_widget.apply_effect(effect_name, params)
                
            elif effect_name == "detect_person":
                enabled = params.get("enabled", False)
                threshold = params.get("threshold", 0.5)
                self.video_widget.enable_person_detection(enabled, threshold)
                
            elif effect_name == "detect_shelves":
                enabled = params.get("enabled", False)
                method = params.get("method", "yolo")
                self.video_widget.enable_shelf_detection(enabled, method)
                
            elif effect_name == "detect_shelves_manual":
                enabled = params.get("enabled", False)
                shelves_count = params.get("shelves_count", 0)
                cells_per_shelf = params.get("cells_per_shelf", 0)
                self.video_widget.enable_shelf_detection_manual(
                    enabled, shelves_count, cells_per_shelf
                )
                
            elif effect_name == "detect_fire":
                enabled = params.get("enabled", False)
                detect_smoke = params.get("detect_smoke", True)
                use_motion = params.get("use_motion", False)
                self.video_widget.enable_fire_detection(enabled, detect_smoke, use_motion)
                
                if enabled:
                    self.info_table.add_row("Детекция", "Поиск возгораний включен", 
                                        f"Дым: {'да' if detect_smoke else 'нет'}, Движение: {'да' if use_motion else 'нет'}")
                else:
                    self.info_table.add_row("Детекция", "Поиск возгораний выключен", "")
    
    def on_fire_detected(self, fires: list, smokes: list):
        """Обработчик обнаружения возгораний"""
        if fires:
            for fire in fires:
                x, y, w, h, _ = fire
                action_name = "🔥 ВОЗГОРАНИЕ"
                details = f"Координаты: ({x}, {y}) размер: {w}x{h}"
                self.info_table.add_row("ОПАСНОСТЬ", action_name, details)
    
    def on_effect_reset(self):
        """Сбрасывает эффекты"""
        if self.video_widget:
            self.video_widget.reset_effects()
    
    def on_table_row_selected(self, row, data):
        """Обработчик выбора строки в таблице"""
        print(f"Выбрана строка {row}: {data}")
    
if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec())