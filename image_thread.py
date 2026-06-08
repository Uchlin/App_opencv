# image_thread.py
from PyQt6.QtCore import QThread, pyqtSignal
from PyQt6.QtGui import QImage, QPixmap
import cv2
import numpy as np

class ImageLoaderThread(QThread):
    """Поток для загрузки и обработки изображений"""
    
    image_loaded = pyqtSignal(QImage)
    image_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        self.image_path = None
        
    def load_image(self, file_path: str):
        """Загружает изображение"""
        self.image_path = file_path
        self.start()
    
    def run(self):
        try:
            # Загружаем изображение через OpenCV
            img = cv2.imread(self.image_path)
            if img is None:
                self.image_error.emit(f"Не удалось загрузить изображение: {self.image_path}")
                return
            
            # Конвертируем BGR в RGB
            img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
            h, w, ch = img_rgb.shape
            bytes_per_line = ch * w
            qt_image = QImage(img_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
            
            self.image_loaded.emit(qt_image.copy())
            
        except Exception as e:
            self.image_error.emit(f"Ошибка загрузки изображения: {str(e)}")