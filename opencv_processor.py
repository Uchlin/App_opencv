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
                
            elif operation == "grayscale":
                processed = self.to_grayscale(processed)
                
            elif operation == "blur":
                kernel_size = params.get("kernel_size", 5) if params else 5
                processed = self.apply_blur(processed, kernel_size)
                
            elif operation == "edge_detection":
                low_threshold = params.get("low_threshold", 50) if params else 50
                high_threshold = params.get("high_threshold", 150) if params else 150
                processed = self.detect_edges(processed, low_threshold, high_threshold)
                
            elif operation == "brightness":
                value = params.get("value", 30) if params else 30
                processed = self.adjust_brightness(processed, value)
                
            elif operation == "contrast":
                alpha = params.get("alpha", 1.5) if params else 1.5
                processed = self.adjust_contrast(processed, alpha)
                
            elif operation == "resize":
                width = params.get("width", 640) if params else 640
                height = params.get("height", 480) if params else 480
                processed = self.resize_frame(processed, width, height)
                
            elif operation == "rotate":
                angle = params.get("angle", 90) if params else 90
                processed = self.rotate_frame(processed, angle)
                
            elif operation == "flip":
                flip_code = params.get("flip_code", 1) if params else 1  # 0=вертикально, 1=горизонтально, -1=оба
                processed = self.flip_frame(processed, flip_code)
                
            elif operation == "threshold":
                threshold_value = params.get("threshold", 127) if params else 127
                max_value = params.get("max_value", 255) if params else 255
                processed = self.apply_threshold(processed, threshold_value, max_value)
                
            elif operation == "canny":
                low = params.get("low", 50) if params else 50
                high = params.get("high", 150) if params else 150
                processed = self.canny_edge(processed, low, high)
                
            elif operation == "contours":
                processed = self.draw_contours(processed)
                
            elif operation == "face_detection":
                processed = self.detect_faces(processed)
                
            elif operation == "sepia":
                processed = self.apply_sepia(processed)
                
            elif operation == "negative":
                processed = self.apply_negative(processed)
                
            return processed
            
        except Exception as e:
            self.processing_error.emit(f"Ошибка обработки: {str(e)}")
            return frame
    
    # Основные операции обработки
    
    def to_grayscale(self, frame):
        """Преобразует в оттенки серого"""
        if len(frame.shape) == 3:
            return cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        return frame
    
    def apply_blur(self, frame, kernel_size=5):
        """Применяет размытие"""
        if kernel_size % 2 == 0:
            kernel_size += 1
        return cv2.GaussianBlur(frame, (kernel_size, kernel_size), 0)
    
    def detect_edges(self, frame, low_threshold=50, high_threshold=150):
        """Детектирует границы (Canny)"""
        # Преобразуем в оттенки серого если нужно
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        edges = cv2.Canny(gray, low_threshold, high_threshold)
        # Конвертируем обратно в BGR для отображения
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    def adjust_brightness(self, frame, value=30):
        """Регулирует яркость"""
        # value может быть от -255 до 255
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        hsv[:, :, 2] = cv2.add(hsv[:, :, 2], value)
        return cv2.cvtColor(hsv, cv2.COLOR_HSV2BGR)
    
    def adjust_contrast(self, frame, alpha=1.5):
        """Регулирует контрастность"""
        # alpha > 1 увеличивает контраст, alpha < 1 уменьшает
        return cv2.convertScaleAbs(frame, alpha=alpha, beta=0)
    
    def resize_frame(self, frame, width, height):
        """Изменяет размер кадра"""
        return cv2.resize(frame, (width, height))
    
    def rotate_frame(self, frame, angle=90):
        """Поворачивает кадр"""
        if angle == 90:
            return cv2.rotate(frame, cv2.ROTATE_90_CLOCKWISE)
        elif angle == 180:
            return cv2.rotate(frame, cv2.ROTATE_180)
        elif angle == 270:
            return cv2.rotate(frame, cv2.ROTATE_90_COUNTERCLOCKWISE)
        else:
            # Произвольный угол
            height, width = frame.shape[:2]
            center = (width // 2, height // 2)
            matrix = cv2.getRotationMatrix2D(center, angle, 1.0)
            return cv2.warpAffine(frame, matrix, (width, height))
    
    def flip_frame(self, frame, flip_code=1):
        """Отражает кадр"""
        # flip_code: 0 = вертикально, 1 = горизонтально, -1 = оба
        return cv2.flip(frame, flip_code)
    
    def apply_threshold(self, frame, threshold_value=127, max_value=255):
        """Применяет пороговую обработку"""
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        _, thresholded = cv2.threshold(gray, threshold_value, max_value, cv2.THRESH_BINARY)
        return cv2.cvtColor(thresholded, cv2.COLOR_GRAY2BGR)
    
    def canny_edge(self, frame, low_threshold=50, high_threshold=150):
        """Детектирует границы с помощью Canny (цветное)"""
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
        edges = cv2.Canny(gray, low_threshold, high_threshold)
        return cv2.cvtColor(edges, cv2.COLOR_GRAY2BGR)
    
    def draw_contours(self, frame):
        """Рисует контуры объектов"""
        if len(frame.shape) == 3:
            gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        else:
            gray = frame
            
        # Находим контуры
        contours, _ = cv2.findContours(gray, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Рисуем контуры
        result = frame.copy()
        cv2.drawContours(result, contours, -1, (0, 255, 0), 2)
        return result
    
    def detect_faces(self, frame):
        """Детектирует лица (требует файл haarcascade_frontalface_default.xml)"""
        try:
            # Загружаем классификатор
            face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            
            if len(frame.shape) == 3:
                gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            else:
                gray = frame
                
            faces = face_cascade.detectMultiScale(gray, 1.1, 5)
            
            # Рисуем прямоугольники вокруг лиц
            result = frame.copy()
            for (x, y, w, h) in faces:
                cv2.rectangle(result, (x, y), (x+w, y+h), (0, 255, 0), 2)
                
            return result
        except Exception as e:
            self.processing_error.emit(f"Ошибка детекции лиц: {str(e)}")
            return frame
    
    def apply_sepia(self, frame):
        """Применяет сепия эффект"""
        result = frame.copy()
        # Матрица преобразования для сепии
        kernel = np.array([[0.272, 0.534, 0.131],
                           [0.349, 0.686, 0.168],
                           [0.393, 0.769, 0.189]])
        result = cv2.transform(result, kernel)
        result = np.clip(result, 0, 255).astype(np.uint8)
        return result
    
    def apply_negative(self, frame):
        """Применяет негатив"""
        return cv2.bitwise_not(frame)
    
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
    def qimage_to_numpy(self, qimage):
        """Конвертирует QImage в numpy array (для OpenCV)"""
        if qimage.isNull():
            return None
        
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
    def numpy_to_qimage(self, frame):
        """Конвертирует numpy array (OpenCV) в QImage"""
        if frame is None:
            return None
        
        # Конвертируем BGR в RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = rgb_frame.shape
        bytes_per_line = 3 * width
        
        return QImage(rgb_frame.data, width, height, bytes_per_line, QImage.Format.Format_RGB888)