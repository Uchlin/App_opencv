import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal
from PyQt6.QtGui import QImage

class OpenCVProcessor(QObject):
    """Класс для обработки изображений и видео с помощью OpenCV"""
    
    # Сигналы
    processing_finished = pyqtSignal(object)  # Отправляет обработанное изображение
    processing_error = pyqtSignal(str)        # Отправляет ошибку
    
    def __init__(self):
        super().__init__()
        
    def process_frame(self, frame, operation="none", params=None):
        """
        Обрабатывает кадр выбранной операцией
        
        Args:
            frame: numpy array (кадр из OpenCV)
            operation: строка с названием операции
            params: дополнительные параметры для операции
        
        Returns:
            обработанный кадр
        """
        if frame is None:
            return None
            
        try:
            # Копируем кадр, чтобы не изменять оригинал
            processed = frame.copy()
            
            # Выбираем операцию
            if operation == "none":
                return processed
                
            elif operation == "all":
                # Применяем эффекты последовательно
                if params and "brightness" in params:
                    processed = self.adjust_brightness(processed, params["brightness"])
                if params and "contrast" in params:
                    processed = self.adjust_contrast(processed, params["contrast"])
                if params and "sharpness" in params:
                    processed = self.adjust_sharpness(processed, params["sharpness"])
                return processed
            
        except Exception as e:
            self.processing_error.emit(f"Ошибка обработки: {str(e)}")
            return frame
    
    # Основные операции обработки
    
    def adjust_brightness(self, frame, value=0):
        """Регулирует яркость через гамма-коррекцию"""
        # value от -100 до 100, преобразуем в гамму от 0.5 до 1.5
        # Отрицательные значения = затемнение, положительные = осветление
        if value >= 0:
            gamma = 1.0 - (value / 200.0)  # 0.5 до 1.0 для осветления
        else:
            gamma = 1.0 - (value / 100.0)  # 1.0 до 2.0 для затемнения
        
        # Гамма-коррекция
        look_up_table = np.array([((i / 255.0) ** gamma) * 255 for i in range(256)]).astype(np.uint8)
        result = cv2.LUT(frame, look_up_table)
        
        return result
    
    def adjust_contrast(self, frame, alpha=1.0):
        """Регулирует контрастность"""
        # alpha > 1 увеличивает контраст, alpha < 1 уменьшает
        # alpha = 0.5 (минимальный) до 2.0 (максимальный)
        return cv2.convertScaleAbs(frame, alpha=alpha, beta=0)
    
    def adjust_sharpness(self, frame, amount=0):
        if amount == 0:
            return frame
        
        # amount от 0 до 100
        # Используем квадратичную зависимость для лучшего контроля
        strength = (amount / 100.0) ** 1.5 * 3.0  # 0 до 3
        
        # Размытие для получения маски
        blurred = cv2.GaussianBlur(frame, (0, 0), 3)
        
        # Добавляем разницу обратно (метод unsharp masking)
        sharpened = cv2.addWeighted(frame, 1.0 + strength, blurred, -strength, 0)
        
        return np.clip(sharpened, 0, 255).astype(np.uint8)
    
    def resize_frame(self, frame, width, height):
        """Изменяет размер кадра"""
        return cv2.resize(frame, (width, height))
    
    # Дополнительные полезные методы
    
    def add_text_to_frame(self, frame, text, position=(50, 50), 
                          font_scale=1, color=(0, 255, 0), thickness=2):
        """Добавляет текст на кадр"""
        result = frame.copy()
        cv2.putText(result, text, position, cv2.FONT_HERSHEY_SIMPLEX, 
                   font_scale, color, thickness)
        return result
    
    def draw_rectangle(self, frame, start_point=(100, 100), end_point=(200, 200),
                      color=(0, 255, 0), thickness=2):
        """Рисует прямоугольник на кадре"""
        result = frame.copy()
        cv2.rectangle(result, start_point, end_point, color, thickness)
        return result
    
    def draw_circle(self, frame, center=(150, 150), radius=50,
                   color=(0, 0, 255), thickness=2):
        """Рисует круг на кадре"""
        result = frame.copy()
        cv2.circle(result, center, radius, color, thickness)
        return result
    
    
    def numpy_to_qimage(self, frame):
        """Конвертирует numpy array (OpenCV) в QImage"""
        if frame is None:
            return None
        
        try:
            # Конвертируем BGR в RGB
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            height, width, channel = rgb_frame.shape
            bytes_per_line = 3 * width
            
            return QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)
        except Exception as e:
            print(f"Ошибка конвертации в QImage: {e}")
            return None
    def qimage_to_numpy(self, qimage):
        """Конвертирует QImage в numpy array (для OpenCV)"""
        if qimage is None or qimage.isNull():
            return None
        
        try:
            # Конвертируем в RGB888 формат
            qimage = qimage.convertToFormat(QImage.Format.Format_RGB888)
            width = qimage.width()
            height = qimage.height()
            
            # Получаем данные
            ptr = qimage.bits()
            ptr.setsize(qimage.sizeInBytes())
            
            # Создаем numpy array
            arr = np.array(ptr).reshape(height, width, 3)
            
            # Конвертируем RGB в BGR (для OpenCV)
            return cv2.cvtColor(arr, cv2.COLOR_RGB2BGR)
        except Exception as e:
            print(f"Ошибка конвертации из QImage: {e}")
            return None