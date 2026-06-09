import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage

class OpenCVProcessor(QObject):
    """Класс для обработки изображений и видео с помощью OpenCV"""
    
    processing_finished = pyqtSignal(object)
    processing_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
    def process_frame(self, frame, operation="none", params=None):
        """
        Обрабатывает кадр выбранной операцией
        """
        if frame is None:
            return None
            
        try:
            processed = frame.copy()
            
            if operation == "none":
                return processed
                
            elif operation == "all":
                # ПРИМЕНЯЕМ ЭФФЕКТЫ ПОСЛЕДОВАТЕЛЬНО
                if params:
                    # Яркость
                    if "brightness" in params and params["brightness"] != 0:
                        brightness_val = params["brightness"]
                        # Преобразуем значение (-100..100) в beta (-100..100)
                        beta = brightness_val
                        processed = cv2.convertScaleAbs(processed, alpha=1.0, beta=beta)
                    
                    # Контрастность
                    if "contrast" in params:
                        contrast_val = params["contrast"]
                        # Преобразуем значение в alpha (0.5..2.0)
                        # contrast_val приходит как число (0.5..2.0) из effects_widget
                        if isinstance(contrast_val, (int, float)):
                            alpha = contrast_val
                        else:
                            # Если пришло как -100..100
                            alpha = 0.5 + (contrast_val + 100) / 200 * 1.5
                        processed = cv2.convertScaleAbs(processed, alpha=alpha, beta=0)
                    
                    # Резкость
                    if "sharpness" in params and params["sharpness"] > 0:
                        sharpness_val = params["sharpness"]
                        # strength от 0 до 3
                        strength = (sharpness_val / 100.0) ** 1.5 * 3.0
                        if strength > 0:
                            blurred = cv2.GaussianBlur(processed, (0, 0), 3)
                            processed = cv2.addWeighted(processed, 1.0 + strength, blurred, -strength, 0)
                            processed = np.clip(processed, 0, 255).astype(np.uint8)
                
                return processed
            
            return processed
            
        except Exception as e:
            self.processing_error.emit(f"Ошибка обработки: {str(e)}")
            return frame
    
    def adjust_brightness(self, frame, value=0):
        """Регулирует яркость"""
        # value от -100 до 100
        return cv2.convertScaleAbs(frame, alpha=1.0, beta=value)
    
    def adjust_contrast(self, frame, alpha=1.0):
        """Регулирует контрастность"""
        return cv2.convertScaleAbs(frame, alpha=alpha, beta=0)
    
    def adjust_sharpness(self, frame, amount=0):
        """Регулирует резкость"""
        if amount <= 0:
            return frame
        
        strength = (amount / 100.0) ** 1.5 * 3.0
        blurred = cv2.GaussianBlur(frame, (0, 0), 3)
        sharpened = cv2.addWeighted(frame, 1.0 + strength, blurred, -strength, 0)
        return np.clip(sharpened, 0, 255).astype(np.uint8)
    
    def resize_frame(self, frame, width, height):
        return cv2.resize(frame, (width, height))
    
    def numpy_to_qimage(self, frame):
        """Конвертирует numpy array в QImage"""
        if frame is None:
            return None
        
        try:
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width
            
            return QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        except Exception as e:
            print(f"Ошибка конвертации в QImage: {e}")
            return None
    
    def qimage_to_numpy(self, qimage):
        """Конвертирует QImage в numpy array"""
        if qimage is None or qimage.isNull():
            return None
        
        try:
            qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)
            width = qimage.width()
            height = qimage.height()
            
            ptr = qimage.bits()
            ptr.setsize(qimage.sizeInBytes())
            
            arr = np.array(ptr).reshape(height, width, 3)
            return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Ошибка конвертации из QImage: {e}")
            return None