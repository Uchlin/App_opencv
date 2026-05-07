# video_thread.py
import sys
from PyQt6.QtCore import QThread, pyqtSignal, Qt, QMutex, QWaitCondition
from PyQt6.QtGui import QImage, QPixmap

# Попробуем импортировать OpenCV, но сделаем это опциональным
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Предупреждение: OpenCV не установлен. Видео будет работать через imageio.")
    import imageio

class VideoPlayerThread(QThread):
    """Поток для воспроизведения видео через QLabel"""
    
    # Сигналы для связи с главным потоком
    frame_ready = pyqtSignal(QImage)
    video_loaded = pyqtSignal(bool, str)
    video_finished = pyqtSignal()
    duration_updated = pyqtSignal(int)
    position_updated = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        self.video_path = None
        self.is_playing = False
        self.is_paused = False
        self.should_stop = False  # Новый флаг для остановки
        self.cap = None
        self.reader = None
        self.fps = 30
        self.frame_delay = 33
        self.total_frames = 0
        self.current_frame = 0
        self.mutex = QMutex()
        self.wait_condition = QWaitCondition()
        
    def load_video(self, file_path: str) -> bool:
        """Загружает видео файл"""
        self.stop()  # Останавливаем текущее воспроизведение
        
        self.video_path = file_path
        
        try:
            if OPENCV_AVAILABLE:
                # Используем OpenCV для загрузки видео
                self.cap = cv2.VideoCapture(file_path)
                if not self.cap.isOpened():
                    self.video_loaded.emit(False, f"Не удалось открыть видео: {file_path}")
                    return False
                
                # Получаем информацию о видео
                self.fps = self.cap.get(cv2.CAP_PROP_FPS)
                if self.fps <= 0:
                    self.fps = 30
                self.total_frames = int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT))
                self.frame_delay = int(1000 / self.fps) if self.fps > 0 else 33
                
            else:
                # Альтернативный способ без OpenCV
                self.reader = imageio.get_reader(file_path)
                meta = self.reader.get_meta_data()
                self.fps = meta.get('fps', 30)
                self.frame_delay = int(1000 / self.fps) if self.fps > 0 else 33
                try:
                    self.total_frames = self.reader.count_frames()
                except:
                    self.total_frames = 0
                    
            self.video_loaded.emit(True, f"Видео загружено: {file_path}")
            self.duration_updated.emit(self.total_frames)
            return True
            
        except Exception as e:
            self.video_loaded.emit(False, f"Ошибка загрузки видео: {str(e)}")
            return False
    
    def run(self):
        """Основной цикл воспроизведения видео"""
        if not self.video_path:
            return
        
        # Сбрасываем флаги перед началом
        self.should_stop = False
        self.is_playing = True
        self.is_paused = False
        self.current_frame = 0
        
        # Перематываем на начало
        if OPENCV_AVAILABLE and self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, 0)
        elif not OPENCV_AVAILABLE and self.reader:
            # Пересоздаём reader для перемотки в начало
            self.reader.close()
            self.reader = imageio.get_reader(self.video_path)
        self.position_updated.emit(0)
        while not self.should_stop:
            # Пауза
            while self.is_paused and not self.should_stop:
                self.msleep(100)
            
            if self.should_stop:
                break
                
            try:
                # Читаем кадр
                frame = None
                if OPENCV_AVAILABLE and self.cap:
                    ret, frame = self.cap.read()
                    if not ret:
                        # Видео закончилось
                        self.video_finished.emit()
                        break
                        
                    # Конвертируем BGR в RGB
                    frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    h, w, ch = frame_rgb.shape
                    bytes_per_line = ch * w
                    qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                    
                elif not OPENCV_AVAILABLE and self.reader:
                    # Используем imageio
                    try:
                        frame = self.reader.get_next_data()
                        if frame.shape[-1] == 4:  # RGBA
                            frame_rgb = frame[:, :, :3]
                        else:
                            frame_rgb = frame
                            
                        h, w, ch = frame_rgb.shape
                        qt_image = QImage(frame_rgb.data, w, h, w * ch, QImage.Format.Format_RGB888)
                    except (StopIteration, IndexError):
                        self.video_finished.emit()
                        break
                else:
                    break
                
                # Отправляем кадр в главный поток
                self.frame_ready.emit(qt_image.copy())
                self.current_frame += 1
                self.position_updated.emit(self.current_frame)
                
                # Задержка для поддержания правильной скорости видео
                self.msleep(self.frame_delay)
                
            except Exception as e:
                print(f"Ошибка при чтении кадра: {e}")
                break
        
        # Очистка ресурсов
        self.cleanup()
    
    def cleanup(self):
        """Очищает ресурсы"""
        if OPENCV_AVAILABLE and self.cap:
            self.cap.release()
            self.cap = None
        elif not OPENCV_AVAILABLE and self.reader:
            self.reader.close()
            self.reader = None
            
    def play(self):
        """Начинает или возобновляет воспроизведение"""
        if not self.isRunning():
            # Если поток не запущен, запускаем новый
            self.should_stop = False
            self.is_paused = False
            self.start()
        elif self.is_paused:
            # Если на паузе, просто снимаем паузу
            self.is_paused = False
            
    def pause(self):
        """Приостанавливает воспроизведение"""
        if self.isRunning() and not self.is_paused:
            self.is_paused = True
            
    def stop(self):
        """Останавливает воспроизведение и сбрасывает позицию"""
        self.should_stop = True
        self.is_playing = False
        self.is_paused = False
        
        # Ждём завершения потока
        if self.isRunning():
            self.quit()
            self.wait(1000)  # Ждём максимум 1 секунду
            
        # Очищаем ресурсы
        self.cleanup()
        self.current_frame = 0
            
    def set_position(self, frame_number: int):
        """Устанавливает позицию воспроизведения (в кадрах)"""
        if OPENCV_AVAILABLE and self.cap:
            # Приостанавливаем воспроизведение на время перемотки
            was_paused = self.is_paused
            was_playing = self.isRunning() and not self.is_paused
            
            if was_playing:
                self.pause()
            
            # Перематываем
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            self.current_frame = frame_number
            self.position_updated.emit(self.current_frame)
            
            # Если нужно получить текущий кадр для отображения
            ret, frame = self.cap.read()
            if ret:
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                self.frame_ready.emit(qt_image.copy())
            
            # Возвращаемся на предыдущий кадр, так как мы прочитали следующий
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, frame_number)
            
            # Возобновляем воспроизведение если было
            if was_playing:
                self.play()