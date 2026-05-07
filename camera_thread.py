# camera_thread.py
import sys
import os
import warnings

# Подавляем предупреждения
warnings.filterwarnings('ignore')

# Отключаем логи OpenCV
os.environ['OPENCV_LOG_LEVEL'] = 'ERROR'
os.environ['OPENCV_FFMPEG_LOGLEVEL'] = '-8'
os.environ['OPENCV_VIDEOIO_DEBUG'] = '0'

from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage

try:
    import cv2
    OPENCV_AVAILABLE = True
except ImportError:
    OPENCV_AVAILABLE = False
    print("Предупреждение: OpenCV не установлен. Установите: pip install opencv-python")

class CameraThread(QThread):
    """Поток для захвата видео с камеры"""
    
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
        
    def start_camera(self):
        """Запускает камеру"""
        if not OPENCV_AVAILABLE:
            self.camera_error.emit("OpenCV не установлен")
            return False
            
        if self.is_running:
            return True
            
        try:
            # Открываем камеру с DSHOW
            if sys.platform == 'win32':
                self.cap = cv2.VideoCapture(self.camera_id, cv2.CAP_DSHOW)
            else:
                self.cap = cv2.VideoCapture(self.camera_id)
                
            if not self.cap or not self.cap.isOpened():
                self.camera_error.emit(f"Не удалось открыть камеру {self.camera_id}")
                return False
            
            # Настраиваем параметры
            self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
            self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
            self.cap.set(cv2.CAP_PROP_FPS, 30)
            
            # Запускаем поток
            self.should_stop = False
            self.is_running = True
            self.start()
            self.camera_started.emit()
            return True
            
        except Exception as e:
            self.camera_error.emit(f"Ошибка: {str(e)}")
            return False
            
    def stop_camera(self):
        """Останавливает камеру"""
        self.should_stop = True
        self.is_running = False
        
        if self.isRunning():
            self.quit()
            self.wait(1000)
            
        if self.cap:
            self.cap.release()
            self.cap = None
            
        self.camera_stopped.emit()
        
    def run(self):
        """Цикл захвата кадров"""
        while not self.should_stop and self.cap and self.cap.isOpened():
            try:
                ret, frame = self.cap.read()
                if not ret or frame is None:
                    self.msleep(10)
                    continue
                
                # Конвертируем BGR в RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                # Отправляем кадр
                self.frame_ready.emit(qt_image.copy())
                
                # Задержка для 30 FPS
                self.msleep(33)
                
            except Exception as e:
                print(f"Ошибка захвата: {e}")
                break
                
        self.is_running = False