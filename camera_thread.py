# camera_thread.py
import sys
from PyQt6.QtCore import QThread, pyqtSignal, QMutex, QWaitCondition
from PyQt6.QtGui import QImage

# Попробуем импортировать OpenCV
try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Предупреждение: OpenCV не установлен. Камера не будет работать.")
    print("Установите OpenCV: pip install opencv-python")

class CameraThread(QThread):
    """Поток для захвата видео с камеры"""
    
    # Сигналы для связи с главным потоком
    frame_ready = pyqtSignal(QImage)
    camera_error = pyqtSignal(str)
    camera_started = pyqtSignal()
    camera_stopped = pyqtSignal()
    
    def __init__(self, camera_id=0):
        super().__init__()
        self.camera_id = camera_id
        self.cap = None
        self.is_running = False
        self.should_stop = False
        self.fps = 30
        self.frame_delay = int(1000 / self.fps)
        
    def start_camera(self):
        """Запускает захват с камеры"""
        if not OPENCV_AVAILABLE:
            self.camera_error.emit("OpenCV не установлен. Установите opencv-python")
            return False
            
        if self.is_running:
            return True
            
        try:
            # Открываем камеру
            self.cap = cv2.VideoCapture(self.camera_id)
            if not self.cap.isOpened():
                self.camera_error.emit(f"Не удалось открыть камеру {self.camera_id}")
                return False
            
            # Получаем FPS камеры (если доступно)
            self.fps = self.cap.get(cv2.CAP_PROP_FPS)
            if self.fps <= 0:
                self.fps = 30
            self.frame_delay = int(1000 / self.fps) if self.fps > 0 else 33
            
            # Запускаем поток
            self.should_stop = False
            self.is_running = True
            self.start()
            self.camera_started.emit()
            return True
            
        except Exception as e:
            self.camera_error.emit(f"Ошибка при запуске камеры: {str(e)}")
            return False
            
    def stop_camera(self):
        """Останавливает захват с камеры"""
        self.should_stop = True
        self.is_running = False
        
        # Ждём завершения потока
        if self.isRunning():
            self.quit()
            self.wait(1000)
            
        # Освобождаем камеру
        if self.cap:
            self.cap.release()
            self.cap = None
            
        self.camera_stopped.emit()
        
    def run(self):
        """Основной цикл захвата кадров с камеры"""
        while not self.should_stop and self.cap and self.cap.isOpened():
            try:
                # Читаем кадр
                ret, frame = self.cap.read()
                if not ret:
                    # Если кадр не прочитался, возможно камера отключилась
                    self.camera_error.emit("Потеряно соединение с камерой")
                    break
                
                # Конвертируем BGR в RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                # Отправляем кадр в главный поток
                self.frame_ready.emit(qt_image.copy())
                
                # Задержка для поддержания правильной скорости
                self.msleep(self.frame_delay)
                
            except Exception as e:
                print(f"Ошибка при захвате кадра: {e}")
                break
                
        # Очистка
        self.is_running = False
        if self.cap:
            self.cap.release()
            self.cap = None