# video_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
from video_thread import VideoPlayerThread

class VideoWidget(QWidget):
    """Виджет для отображения и управления видео"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.video_thread = None
        self.current_video_path = None
        self.setup_ui()
        
    def setup_ui(self):
        """Создаёт интерфейс виджета"""
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Метка для отображения видео
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: black;
                border: 2px solid #333;
                border-radius: 5px;
                min-height: 400px;
            }
        """)
        layout.addWidget(self.video_label)
        
        # Нижняя панель управления
        controls_widget = QWidget()
        controls_layout = QHBoxLayout(controls_widget)
        controls_layout.setContentsMargins(5, 5, 5, 5)
        
        # Кнопки управления
        self.play_btn = QPushButton("▶ Play")
        self.play_btn.setEnabled(False)
        self.play_btn.clicked.connect(self.play_video)
        
        self.pause_btn = QPushButton("⏸ Pause")
        self.pause_btn.setEnabled(False)
        self.pause_btn.clicked.connect(self.pause_video)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_video)
        
        controls_layout.addWidget(self.play_btn)
        controls_layout.addWidget(self.pause_btn)
        controls_layout.addWidget(self.stop_btn)
        
        # Слайдер позиции
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setEnabled(False)
        self.position_slider.sliderMoved.connect(self.seek_video)
        controls_layout.addWidget(self.position_slider)
        
        # Метка времени
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)
        controls_layout.addWidget(self.time_label)
        
        layout.addWidget(controls_widget)
        self.setLayout(layout)
        
        # Изначально виджет скрыт
        self.show_placeholder()
    def show_placeholder(self):
        """Показывает заглушку, когда видео не загружено"""
        self.video_label.setText(
            "🎬 Готов к работе\n\n"
            "Чтобы начать:\n"
            "1. Нажмите 'Файл' → 'Открыть...'\n"
            "2. Выберите видео файл"
        )
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: black;
                color: white;
                font-size: 16px;
                border: 2px solid #333;
                border-radius: 5px;
                min-height: 400px;
            }
        """)
        self.update_buttons_state(stopped=True)
        
    def init_video_thread(self):
        """Инициализирует новый поток для видео"""
        # Останавливаем и удаляем старый поток если есть
        if self.video_thread:
            self.video_thread.stop()
            self.video_thread.deleteLater()
            
        # Создаём новый поток
        self.video_thread = VideoPlayerThread()
        
        # Подключаем сигналы
        self.video_thread.frame_ready.connect(self.display_frame)
        self.video_thread.video_loaded.connect(self.on_video_loaded)
        self.video_thread.video_finished.connect(self.on_video_finished)
        self.video_thread.duration_updated.connect(self.on_duration_updated)
        self.video_thread.position_updated.connect(self.on_position_updated)
        
    def load_video(self, file_path: str):
        """Загружает видео файл"""
        self.current_video_path = file_path
        self.init_video_thread()
        
        # Показываем виджет, если он был скрыт
        self.show()
        
        # Показываем индикатор загрузки
        self.video_label.setText("Загрузка видео...")
        
        # Загружаем видео
        if self.video_thread.load_video(file_path):
            # Автоматически начинаем воспроизведение
            self.play_video()
        else:
            self.video_label.setText("Ошибка загрузки видео")
            
    def play_video(self):
        """Начинает или возобновляет воспроизведение"""
        if not self.current_video_path:
            return
            
        # Если потока нет или он остановлен, создаём новый
        if not self.video_thread or not self.video_thread.isRunning():
            self.init_video_thread()
            if self.video_thread.load_video(self.current_video_path):
                self.video_thread.play()
                self.update_buttons_state(playing=True)
            else:
                self.video_label.setText("Ошибка загрузки видео")
        else:
            # Если поток существует, просто играем
            self.video_thread.play()
            self.update_buttons_state(playing=True)
            
    def pause_video(self):
        """Приостанавливает воспроизведение"""
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.pause()
            self.update_buttons_state(paused=True)
            
    def stop_video(self):
        """Останавливает воспроизведение и сбрасывает позицию"""
        if self.video_thread:
            self.video_thread.stop()
            # Не удаляем поток полностью, просто сбрасываем состояние
            self.update_buttons_state(stopped=True)
            self.video_label.clear()
            self.video_label.setText("Воспроизведение остановлено\nНажмите Play для начала")
            self.time_label.setText("00:00 / 00:00")
            self.position_slider.setValue(0)
            
            # Помечаем, что поток нужно будет пересоздать при следующем play
            self.current_frame = 0
            
    def update_buttons_state(self, playing=False, paused=False, stopped=False):
        """Обновляет состояние кнопок"""
        if playing:
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.position_slider.setEnabled(True)
        elif paused:
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(True)
            self.position_slider.setEnabled(True)
        elif stopped:
            self.play_btn.setEnabled(True)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.position_slider.setEnabled(False)
            
    def seek_video(self, position):
        """Перемещает позицию воспроизведения"""
        if self.video_thread and self.video_thread.isRunning():
            self.video_thread.set_position(position)
            
    def display_frame(self, qt_image):
        """Отображает кадр на QLabel"""
        if not qt_image.isNull() and self.video_label:
            try:
                # Преобразуем QImage в QPixmap
                pixmap = QPixmap.fromImage(qt_image)
                
                # Масштабируем изображение под размер QLabel
                if not pixmap.isNull():
                    scaled_pixmap = pixmap.scaled(
                        self.video_label.size(),
                        Qt.AspectRatioMode.KeepAspectRatio,
                        Qt.TransformationMode.SmoothTransformation
                    )
                    self.video_label.setPixmap(scaled_pixmap)
            except Exception as e:
                print(f"Ошибка отображения кадра: {e}")
            
    def on_video_loaded(self, success, message):
        """Обработчик события загрузки видео"""
        if not success:
            self.video_label.setText(f"Ошибка: {message}")
            self.play_btn.setEnabled(False)
            self.pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
        else:
            # Видео успешно загружено
            pass
            
    def on_video_finished(self):
        """Обработчик окончания видео"""
        # Видео закончилось, останавливаем и сбрасываем на начало
        if self.video_thread:
            self.video_thread.stop()
            self.update_buttons_state(stopped=True)
            self.video_label.setText("Видео закончилось\nНажмите Play для повтора")
            self.position_slider.setValue(0)
            self.time_label.setText("00:00 / 00:00")
            
            # Сбрасываем позицию
            self.current_frame = 0
            
    def on_duration_updated(self, total_frames):
        """Обновляет информацию о длительности видео"""
        if total_frames > 0 and self.video_thread and self.video_thread.fps > 0:
            self.position_slider.setRange(0, total_frames)
            
    def on_position_updated(self, current_frame):
        """Обновляет отображение текущей позиции"""
        if not self.position_slider.isSliderDown() and self.video_thread:
            self.position_slider.setValue(current_frame)
            
        if self.video_thread and self.video_thread.fps > 0:
            current_seconds = current_frame / self.video_thread.fps
            total_seconds = self.video_thread.total_frames / self.video_thread.fps if self.video_thread.total_frames > 0 else 0
            self.time_label.setText(f"{self.format_time(current_seconds)} / {self.format_time(total_seconds)}")
            
    def format_time(self, seconds):
        """Конвертирует секунды в формат MM:SS"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
        
    def resizeEvent(self, event):
        """Обработчик изменения размера виджета"""
        super().resizeEvent(event)
        # При изменении размера виджета видео автоматически перемасштабируется
        # при следующем кадре через display_frame
    