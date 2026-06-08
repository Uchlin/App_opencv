# video_widget.py (обновленная версия)
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QSlider, QHBoxLayout, QPushButton
from PyQt6.QtCore import Qt, QTimer, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2
from image_thread import ImageLoaderThread
from video_thread import VideoPlayerThread
from camera_thread import CameraThread
from opencv_processor import OpenCVProcessor
from person_detector import DetectionThread, PersonDetector
class VideoWidget(QWidget):
    """Виджет для отображения и управления видео и камерой"""
    VIDEO_WIDTH = 320
    VIDEO_HEIGHT = 240
    # Добавляем новые сигналы
    camera_mode_changed = pyqtSignal(bool)  # True = камера, False = видео
    person_detected_signal = pyqtSignal(int, list)  # количество людей, список позиций
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("VideoWidget")
        self.video_thread = None
        self.camera_thread = None
        self.current_video_path = None
        self.image_thread = None
        self.current_image = None
        self.is_image_mode = False
        self.is_camera_mode = False
        self.setAttribute(Qt.WidgetAttribute.WA_StyledBackground, True)
        self.setup_ui()
        total_width = self.VIDEO_WIDTH + 20
        total_height = self.VIDEO_HEIGHT + 80
        self.setFixedSize(total_width, total_height)
        self.setStyleSheet("""
            #VideoWidget {
            border: 2px solid lightgrey;
            border-radius: 5px;
        }
    """)
        self.processor = OpenCVProcessor()
        self.current_operation = "none"
        self.operation_params = {}
        self.person_detector = PersonDetector()
        self.person_detection_enabled = False
        self.detection_threshold = 0.5
        self.last_detection_time = 0
        self.detection_cooldown = 2000  # миллисекунды между записями
        self.current_frame = None # Кадр с нарисованными рамкам
        self.frame_counter = 0  # ДОБАВЬТЕ ДЛЯ ОПТИМИЗАЦИИ
        self.detection_interval = 3  # Каждый N кадр
         # Подключаем сигнал обнаружения
        self.person_detector.person_detected.connect(self.on_people_detected)
        
        # Создаем поток без аргументов
        self.detection_thread = DetectionThread()  # УБРАЛИ АРГУМЕНТЫ
        self.detection_thread.detection_ready.connect(self.on_detection_ready)
    def setup_ui(self):
        """Создаёт интерфейс виджета"""
        layout = QVBoxLayout()
        # Метка для отображения видео/камеры
        self.video_label = QLabel()
        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.video_label.setFixedSize(self.VIDEO_WIDTH, self.VIDEO_HEIGHT)
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: black;
                border: 2px solid #333;
                border-radius: 5px;
            }
        """)
        layout.addWidget(self.video_label, alignment=Qt.AlignmentFlag.AlignCenter)
        # Контейнер для элементов управления (центрируем их)
        controls_container = QWidget()
        controls_container_layout = QVBoxLayout(controls_container)
        controls_container_layout.setContentsMargins(0, 0, 0, 0)
        controls_container_layout.setSpacing(5)
        
        # Слайдер позиции (делаем его по ширине видеоэкрана)
        self.position_slider = QSlider(Qt.Orientation.Horizontal)
        self.position_slider.setEnabled(False)
        self.position_slider.sliderMoved.connect(self.seek_video)
        self.position_slider.setFixedWidth(self.VIDEO_WIDTH)  # Фиксируем ширину слайдера
        controls_container_layout.addWidget(self.position_slider, alignment=Qt.AlignmentFlag.AlignCenter)
        # Контейнер для кнопок и времени
        buttons_widget = QWidget()
        buttons_layout = QHBoxLayout(buttons_widget)
        buttons_layout.setContentsMargins(0, 0, 0, 0)
        buttons_layout.setSpacing(10)
        
        # Кнопки управления
        self.play_pause_btn = QPushButton("▶ Play")
        self.play_pause_btn.setEnabled(False)
        self.play_pause_btn.clicked.connect(self.toggle_play_pause)
        
        self.stop_btn = QPushButton("⏹ Stop")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop_video)
        
        self.stop_camera_btn = QPushButton("📷 Stop Camera")
        self.stop_camera_btn.setEnabled(False)
        self.stop_camera_btn.clicked.connect(self.stop_camera)
        
        buttons_layout.addWidget(self.play_pause_btn)
        buttons_layout.addWidget(self.stop_btn)
        buttons_layout.addWidget(self.stop_camera_btn)
        buttons_layout.addStretch()  # Добавляем растягивание справа
        
        # Метка времени
        self.time_label = QLabel("00:00 / 00:00")
        self.time_label.setMinimumWidth(100)
        buttons_layout.addWidget(self.time_label)
        
        controls_container_layout.addWidget(buttons_widget)
        # Добавляем контейнер с управлением в основной layout, центрируем
        layout.addWidget(controls_container, alignment=Qt.AlignmentFlag.AlignCenter)
        
        self.setLayout(layout)
        self.show_placeholder()
        
    def show_placeholder(self):
        """Показывает заглушку, когда видео не загружено"""
        self.video_label.setFixedSize(self.VIDEO_WIDTH, self.VIDEO_HEIGHT)
        self.video_label.setText(
            "🎬 Готов к работе\n\n"
            "Чтобы начать:\n"
            "1. Нажмите 'Файл' → 'Открыть...' для видео\n"
            "2. Нажмите 'Файл' → 'Камера' для веб-камеры"
        )
        self.video_label.setStyleSheet("""
            QLabel {
                background-color: black;
                color: white;
                font-size: 16px;
                border: 2px solid #333;
                border-radius: 5px;
            }
        """)
        self.update_buttons_state(stopped=True)
        self.stop_camera_btn.setEnabled(False)
        
    def switch_to_camera_mode(self, camera_id=0):
        """Переключается на режим камеры"""
        # Останавливаем текущее видео если оно есть
        self.stop_video()
        
        # Останавливаем камеру если она уже запущена
        if self.camera_thread:
            self.stop_camera()
            
        # Создаём новый поток для камеры
        self.camera_thread = CameraThread(camera_id)
        
        # Подключаем сигналы
        self.camera_thread.frame_ready.connect(self.display_frame)
        self.camera_thread.camera_error.connect(self.on_camera_error)
        self.camera_thread.camera_started.connect(self.on_camera_started)
        self.camera_thread.camera_stopped.connect(self.on_camera_stopped)
        
        # Запускаем камеру
        if self.camera_thread.start_camera():
            self.is_camera_mode = True
            self.camera_mode_changed.emit(True)
            # Скрываем кнопки управления видео
            self.play_pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            self.position_slider.setEnabled(False)
            self.stop_camera_btn.setEnabled(True)
            # Убираем отображение времени
            self.time_label.setText("Камера (Live)")
            self.video_label.setText("Запуск камеры...")
        else:
            self.show_placeholder()
            
    def stop_camera(self):
        """Останавливает трансляцию с камеры"""
        if self.detection_thread and self.detection_thread.isRunning():
            self.detection_thread.stop()
        
        if self.camera_thread:
            self.camera_thread.stop_camera()
            self.camera_thread.deleteLater()
            self.camera_thread = None
            
        self.is_camera_mode = False
        self.camera_mode_changed.emit(False)
        self.show_placeholder()
        
    def on_camera_started(self):
        """Обработчик успешного запуска камеры"""
        self.video_label.setFixedSize(self.VIDEO_WIDTH, self.VIDEO_HEIGHT)
        self.video_label.setText("Камера запущена")
        
    def on_camera_stopped(self):
        """Обработчик остановки камеры"""
        self.show_placeholder()
        
    def on_camera_error(self, error_message):
        """Обработчик ошибок камеры"""
        self.video_label.setText(f"Ошибка камеры: {error_message}")
        self.stop_camera()
        
    def init_video_thread(self):
        """Инициализирует новый поток для видео"""
        # Если в режиме камеры, сначала выключаем камеру
        if self.is_camera_mode:
            self.stop_camera()
            
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
        # Переключаемся в режим видео
        if self.is_camera_mode:
            self.stop_camera()
        self.video_label.setFixedSize(self.VIDEO_WIDTH, self.VIDEO_HEIGHT)
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
    def load_image(self, file_path: str):
        """Загружает изображение"""
        # Останавливаем видео и камеру
        self.stop_video()
        self.stop_camera()
        
        self.current_video_path = file_path
        self.is_image_mode = True
        self.is_camera_mode = False
        
        # Создаем поток для загрузки изображения
        self.image_thread = ImageLoaderThread()
        self.image_thread.image_loaded.connect(self.display_image)
        self.image_thread.image_error.connect(self.on_image_error)
        self.image_thread.load_image(file_path)
        
        # Обновляем UI
        self.time_label.setText("Изображение")
        self.play_pause_btn.setEnabled(False)
        self.stop_btn.setEnabled(True)
        self.position_slider.setEnabled(False)

    def display_image(self, qt_image):
        """Отображает изображение"""
        self.current_image = qt_image
        self.display_frame(qt_image)

    def on_image_error(self, error_message):
        """Обработчик ошибки загрузки изображения"""
        self.video_label.setText(f"Ошибка: {error_message}")
        self.show_placeholder()
    def toggle_play_pause(self):
        """Переключает между воспроизведением и паузой"""
        if not self.is_camera_mode:
            if self.video_thread and self.video_thread.isRunning() and not self.video_thread.is_paused:
                # Видео играет - ставим на паузу
                self.pause_video()
            else:
                # Видео на паузе или остановлено - играем
                self.play_video()
    def play_video(self):
        """Начинает или возобновляет воспроизведение"""
        if self.is_camera_mode:
            return
            
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
        if not self.is_camera_mode and self.video_thread and self.video_thread.isRunning():
            self.video_thread.pause()
            self.update_buttons_state(paused=True)
            
    def stop_video(self):
        """Останавливает воспроизведение"""
        if self.video_thread:
            self.video_thread.stop()
        
        if self.image_thread and self.image_thread.isRunning():
            self.image_thread.quit()
            self.image_thread.wait()
        
        self.is_image_mode = False
        self.video_label.setFixedSize(self.VIDEO_WIDTH, self.VIDEO_HEIGHT)
        self.update_buttons_state(stopped=True)
        self.video_label.clear()
        self.video_label.setText("Воспроизведение остановлено\nНажмите Play для начала")
        self.time_label.setText("00:00 / 00:00")
        self.position_slider.setValue(0)
        self.play_pause_btn.setText("▶ Play")
            
    def update_buttons_state(self, playing=False, paused=False, stopped=False):
        """Обновляет состояние кнопок"""
        if playing:
            self.play_pause_btn.setText("⏸ Pause")
            self.play_pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.position_slider.setEnabled(True)
        elif paused:
            self.play_pause_btn.setText("▶ Play")
            self.play_pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(True)
            self.position_slider.setEnabled(True)
        elif stopped:
            self.play_pause_btn.setText("▶ Play")
            self.play_pause_btn.setEnabled(True)
            self.stop_btn.setEnabled(False)
            self.position_slider.setEnabled(False)
            
    def seek_video(self, position):
        """Перемещает позицию воспроизведения"""
        if not self.is_camera_mode and self.video_thread and self.video_thread.isRunning():
            self.video_thread.set_position(position)
    # Добавьте метод для включения детектора:
    def enable_person_detection(self, enabled, threshold=0.3):
        """Включает/выключает обнаружение людей"""
        self.person_detection_enabled = enabled
        self.detection_threshold = threshold
        self.frame_counter = 0  # Сброс счетчика
        if not enabled:
            self.last_detection_time = 0
        else:
            # Не начинаем детекцию сразу, ждем накопления кадров
            pass

    # Добавьте метод обработки обнаружения:
    def on_people_detected(self, detections):
        """Обработчик обнаружения людей"""
        if not self.person_detection_enabled:
            return
        print(f"[DEBUG] Обнаружено {len(detections)} человек(а)")
        from datetime import datetime
        import time
        
        current_time = time.time() * 1000  # миллисекунды
        
        # Проверяем cooldown, чтобы не спамить в таблицу
        if current_time - self.last_detection_time >= self.detection_cooldown:
            self.last_detection_time = current_time
            count = len(detections)
            
            # Получаем статистику о позициях
            stats = self.person_detector.get_detection_statistics(
                detections, 
                (self.VIDEO_HEIGHT, self.VIDEO_WIDTH)
            )
            
            # Создаем детальное описание
            positions_str = ", ".join(stats["positions"]) if stats["positions"] else "неизвестно"
            
            # Отправляем сигнал в main для записи в таблицу
            self.person_detected_signal.emit(count, stats["positions"])
    def display_frame(self, qt_image):
        """Отображает кадр на QLabel"""
        if not qt_image.isNull() and self.video_label:
            try:
                # Увеличиваем счетчик кадров
                self.frame_counter += 1
                
                current_frame = None
                
                # Если есть активный эффект, обрабатываем кадр
                if hasattr(self, 'current_operation') and self.current_operation != "none":
                    frame = self.processor.qimage_to_numpy(qt_image)
                    if frame is not None:
                        processed_frame = self.processor.process_frame(
                            frame, self.current_operation, self.operation_params
                        )
                        if processed_frame is not None:
                            qt_image = self.processor.numpy_to_qimage(processed_frame)
                            current_frame = processed_frame
                        else:
                            current_frame = frame
                    else:
                        current_frame = None
                else:
                    # Конвертируем для детектора без эффектов
                    current_frame = self.processor.qimage_to_numpy(qt_image)
                
                # Сохраняем текущий кадр для on_detection_ready
                self.current_frame = current_frame
                
                # ОБНАРУЖЕНИЕ ЛЮДЕЙ (только каждый N-кадр)
                if (self.person_detection_enabled and 
                    current_frame is not None and 
                    self.frame_counter % self.detection_interval == 0 and
                    not self.detection_thread.isRunning()):
                    
                    # Уменьшаем кадр для скорости
                    small_frame = cv2.resize(current_frame, (160, 120))
                    self.detection_thread.set_frame(small_frame, self.detection_threshold)
                    self.detection_thread.start()
                
                # Отображаем кадр
                if qt_image is not None and not qt_image.isNull():
                    pixmap = QPixmap.fromImage(qt_image)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            self.video_label.width(),
                            self.video_label.height(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.video_label.setPixmap(scaled_pixmap)
                        self.video_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
                    
            except Exception as e:
                print(f"Ошибка отображения кадра: {e}")
    def on_detection_ready(self, detections):
        """Обработка результатов из потока"""
        if detections and self.current_frame is not None:
            # Масштабируем координаты обратно к исходному размеру
            h, w = self.current_frame.shape[:2]
            scale_x = w / 160
            scale_y = h / 120
            
            scaled_detections = []
            for x, y, dw, dh in detections:
                scaled_detections.append((
                    int(x * scale_x),
                    int(y * scale_y),
                    int(dw * scale_x),
                    int(dh * scale_y)
                ))
            
            # Рисуем рамки на исходном кадре
            if hasattr(self, 'current_frame') and self.current_frame is not None:
                display_frame = self.current_frame.copy()
                for x, y, w, h in scaled_detections:
                    cv2.rectangle(display_frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
                
                # Конвертируем обратно в QImage для отображения
                qt_image = self.processor.numpy_to_qimage(display_frame)
                if qt_image and not qt_image.isNull():
                    pixmap = QPixmap.fromImage(qt_image)
                    if not pixmap.isNull():
                        scaled_pixmap = pixmap.scaled(
                            self.video_label.width(),
                            self.video_label.height(),
                            Qt.AspectRatioMode.KeepAspectRatio,
                            Qt.TransformationMode.SmoothTransformation
                        )
                        self.video_label.setPixmap(scaled_pixmap)
            
            # Отправляем сигнал с количеством
            self.person_detected_signal.emit(len(scaled_detections), scaled_detections)
    def on_video_loaded(self, success, message):
        """Обработчик события загрузки видео"""
        if not success:
            self.video_label.setText(f"Ошибка: {message}")
            self.play_pause_btn.setEnabled(False)
            self.stop_btn.setEnabled(False)
            
    def on_video_finished(self):
        """Обработчик окончания видео"""
        if not self.is_camera_mode and self.video_thread:
            self.video_thread.stop()
            self.update_buttons_state(stopped=True)
            self.video_label.setText("Видео закончилось\nНажмите Play для повтора")
            self.position_slider.setValue(0)
            self.time_label.setText("00:00 / 00:00")
            self.play_pause_btn.setText("▶ Play")
            
    def on_duration_updated(self, total_frames):
        """Обновляет информацию о длительности видео"""
        if total_frames > 0 and self.video_thread and self.video_thread.fps > 0:
            self.position_slider.setRange(0, total_frames)
            
    def on_position_updated(self, current_frame):
        """Обновляет отображение текущей позиции"""
        if not self.is_camera_mode:
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
    def apply_effect(self, operation, params=None):
        """Применяет эффект к текущему видео/камере/изображению"""
        self.current_operation = operation
        self.operation_params = params or {}
        
        # Если открыто изображение, применяем эффект сразу
        if self.is_image_mode and self.current_image:
            frame = self.processor.qimage_to_numpy(self.current_image)
            if frame is not None:
                processed_frame = self.processor.process_frame(
                    frame, operation, params
                )
                if processed_frame is not None:
                    qt_image = self.processor.numpy_to_qimage(processed_frame)
                    self.display_frame(qt_image)
    def reset_effects(self):
        """Сбрасывает все эффекты"""
        # Отключаем эффект
        self.current_operation = "none"
        self.operation_params = {}
    