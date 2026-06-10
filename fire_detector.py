import cv2
import numpy as np
from typing import List, Tuple
from PyQt6.QtCore import QObject, pyqtSignal

class FireDetector(QObject):
    """Класс для обнаружения огня и дыма на видео (только OpenCV)"""
    
    fire_detected = pyqtSignal(list)
    detection_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Минимальная площадь для детекции (пикселей)
        self.min_fire_area = 300
        self.min_smoke_area = 500
        
        # Флаг для отладки
        self.debug = False
        
    def detect_fire(self, frame: np.ndarray, 
                   detect_smoke: bool = True,
                   use_motion: bool = False) -> List[Tuple[int, int, int, int, str]]:
        """
        Обнаружение огня и дыма на кадре
        
        Returns:
            Список областей: [(x, y, w, h, type), ...]
            type: 'fire' или 'smoke'
        """
        if frame is None:
            return []
        
        try:
            detections = []
            
            # Обнаружение огня
            fire_detections = self._detect_fire(frame)
            detections.extend(fire_detections)
            
            # Обнаружение дыма (опционально)
            if detect_smoke:
                smoke_detections = self._detect_smoke(frame)
                detections.extend(smoke_detections)
            
            # Убираем дубликаты
            detections = self._non_max_suppression(detections, threshold=0.5)
            
            if detections and self.debug:
                print(f"[FireDetector] Обнаружено: {len([d for d in detections if d[4]=='fire'])} огня, "
                      f"{len([d for d in detections if d[4]=='smoke'])} дыма")
            
            if detections:
                self.fire_detected.emit(detections)
            
            return detections
            
        except Exception as e:
            self.detection_error.emit(f"Ошибка: {str(e)}")
            return []
    
    def _detect_fire(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, str]]:
        """
        Обнаружение огня по цвету и движению
        """
        detections = []
        
        # 1. Преобразуем в HSV для лучшего выделения цветов
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 2. Диапазоны цветов для огня (оранжевый, красный, жёлтый)
        # Нижний диапазон красного/оранжевого
        lower1 = np.array([0, 120, 100])
        upper1 = np.array([10, 255, 255])
        
        # Верхний диапазон красного
        lower2 = np.array([170, 120, 100])
        upper2 = np.array([180, 255, 255])
        
        # Жёлтый/оранжевый диапазон
        lower3 = np.array([15, 100, 150])
        upper3 = np.array([25, 255, 255])
        
        # Создаём маски
        mask1 = cv2.inRange(hsv, lower1, upper1)
        mask2 = cv2.inRange(hsv, lower2, upper2)
        mask3 = cv2.inRange(hsv, lower3, upper3)
        
        fire_mask = cv2.bitwise_or(mask1, mask2)
        fire_mask = cv2.bitwise_or(fire_mask, mask3)
        
        # 3. Морфологические операции для удаления шума
        kernel = np.ones((5, 5), np.uint8)
        fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_OPEN, kernel)
        fire_mask = cv2.morphologyEx(fire_mask, cv2.MORPH_CLOSE, kernel)
        
        # 4. Находим контуры
        contours, _ = cv2.findContours(fire_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_fire_area:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # 5. Дополнительные проверки для снижения ложных срабатываний
            
            # Проверка 1: Соотношение сторон (огонь обычно вытянут вверх)
            aspect_ratio = h / w if w > 0 else 0
            if aspect_ratio > 4:  # Слишком вытянутый - скорее всего не огонь
                continue
            
            # Проверка 2: Яркость области (огонь очень яркий)
            roi = frame[y:y+h, x:x+w]
            avg_brightness = np.mean(cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY))
            if avg_brightness < 100:  # Слишком тёмное
                continue
            
            # Проверка 3: Насыщенность цвета
            roi_hsv = hsv[y:y+h, x:x+w]
            avg_saturation = np.mean(roi_hsv[:, :, 1])
            if avg_saturation < 100:  # Недостаточно насыщенный
                continue
            
            detections.append((x, y, w, h, 'fire'))
            
            if self.debug:
                print(f"  Огонь: pos=({x},{y}), size={w}x{h}, яркость={avg_brightness:.0f}, насыщ={avg_saturation:.0f}")
        
        return detections
    
    def _detect_smoke(self, frame: np.ndarray) -> List[Tuple[int, int, int, int, str]]:
        """
        Обнаружение дыма по текстуре и цвету
        """
        detections = []
        
        # 1. Преобразуем в разные цветовые пространства
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        hsv = cv2.cvtColor(frame, cv2.COLOR_BGR2HSV)
        
        # 2. Маска для серых/белых областей (дым)
        # Дым обычно серый/белый с низкой насыщенностью
        smoke_lower = np.array([0, 0, 80])
        smoke_upper = np.array([180, 50, 255])
        smoke_mask = cv2.inRange(hsv, smoke_lower, smoke_upper)
        
        # 3. Анализ текстуры - дым имеет низкую контрастность
        blur = cv2.GaussianBlur(gray, (21, 21), 0)
        texture = cv2.absdiff(gray, blur)
        _, texture_mask = cv2.threshold(texture, 10, 255, cv2.THRESH_BINARY)
        texture_mask = cv2.bitwise_not(texture_mask)  # Инвертируем - области с низкой текстурой
        
        # 4. Объединяем маски
        combined_mask = cv2.bitwise_and(smoke_mask, texture_mask)
        
        # 5. Морфология
        kernel = np.ones((7, 7), np.uint8)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_OPEN, kernel)
        combined_mask = cv2.morphologyEx(combined_mask, cv2.MORPH_CLOSE, kernel)
        
        # 6. Находим контуры
        contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        for contour in contours:
            area = cv2.contourArea(contour)
            if area < self.min_smoke_area:
                continue
            
            x, y, w, h = cv2.boundingRect(contour)
            
            # Дополнительные проверки
            roi_gray = gray[y:y+h, x:x+w]
            std_dev = np.std(roi_gray)  # Стандартное отклонение (дым имеет низкое)
            
            if std_dev > 30:  # Слишком высокая вариативность - не дым
                continue
            
            detections.append((x, y, w, h, 'smoke'))
            
            if self.debug:
                print(f"  Дым: pos=({x},{y}), size={w}x{h}, std={std_dev:.0f}")
        
        return detections
    
    def _non_max_suppression(self, detections: List, threshold: float = 0.5) -> List:
        """Подавление не-максимумов для bounding box'ов"""
        if len(detections) <= 1:
            return detections
        
        # Конвертируем в формат (x1, y1, x2, y2, type)
        boxes = [(x, y, x + w, y + h, t) for x, y, w, h, t in detections]
        
        # Сортируем по площади (большие первыми)
        areas = [(x2 - x1) * (y2 - y1) for x1, y1, x2, y2, _ in boxes]
        indices = np.argsort(areas)[::-1]
        
        filtered = []
        
        while len(indices) > 0:
            current = indices[0]
            filtered.append(boxes[current])
            
            remaining = []
            for idx in indices[1:]:
                x1 = max(boxes[current][0], boxes[idx][0])
                y1 = max(boxes[current][1], boxes[idx][1])
                x2 = min(boxes[current][2], boxes[idx][2])
                y2 = min(boxes[current][3], boxes[idx][3])
                
                intersection = max(0, x2 - x1) * max(0, y2 - y1)
                area1 = (boxes[current][2] - boxes[current][0]) * \
                        (boxes[current][3] - boxes[current][1])
                area2 = (boxes[idx][2] - boxes[idx][0]) * \
                        (boxes[idx][3] - boxes[idx][1])
                union = area1 + area2 - intersection
                
                iou = intersection / union if union > 0 else 0
                
                if iou < threshold:
                    remaining.append(idx)
            
            indices = np.array(remaining)
        
        # Конвертируем обратно в формат (x, y, w, h, type)
        return [(x1, y1, x2 - x1, y2 - y1, t) for x1, y1, x2, y2, t in filtered]
    
    def draw_detections(self, frame: np.ndarray, 
                       detections: List[Tuple[int, int, int, int, str]],
                       show_labels: bool = True) -> np.ndarray:
        """Рисует рамки вокруг обнаруженных областей"""
        if frame is None or len(detections) == 0:
            return frame
        
        result = frame.copy()
        
        for x, y, w, h, det_type in detections:
            if det_type == 'fire':
                color = (0, 0, 255)  # Красный
                label = "FIRE"
                thickness = 2
            # elif det_type == 'smoke':
            #     color = (128, 128, 128)  # Серый
            #     label = "SMOKE"
            #     thickness = 2
            else:
                continue
            
            # Рисуем рамку
            cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
            
            if show_labels:
                # Добавляем подпись
                font = cv2.FONT_HERSHEY_SIMPLEX
                font_scale = 0.6
                label_size = cv2.getTextSize(label, font, font_scale, thickness)[0]
                
                # Фон для текста
                cv2.rectangle(result, 
                            (x, y - label_size[1] - 5), 
                            (x + label_size[0] + 5, y), 
                            color, -1)
                
                # Текст
                cv2.putText(result, label, (x + 2, y - 3),
                          font, font_scale, (255, 255, 255), thickness)
        
        return result
    
    def set_debug(self, enabled: bool):
        """Включает/выключает отладку"""
        self.debug = enabled