import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from typing import List, Tuple, Optional

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("YOLO не установлен. Установите: pip install ultralytics")

class PersonDetector(QObject):
    """Класс для обнаружения людей в кадре с использованием YOLO"""
    
    person_detected = pyqtSignal(list)
    detection_error = pyqtSignal(str)
    detection_progress = pyqtSignal(int)
    
    def __init__(self):
        super().__init__()
        
        self.use_yolo = YOLO_AVAILABLE
        self.yolo_model = None  # Не загружаем сразу
        self.model_loaded = False
        
        if not self.use_yolo:
            # HOG и каскады загружаем сразу
            self.hog = cv2.HOGDescriptor()
            self.hog.setSVMDetector(cv2.HOGDescriptor_getDefaultPeopleDetector())
            self.face_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
            )
            self.upper_body_cascade = cv2.CascadeClassifier(
                cv2.data.haarcascades + 'haarcascade_upperbody.xml'
            )
            
            self.win_stride = (4, 4)
            self.padding = (8, 8)
            self.scale = 1.05
        
        self.confidence_threshold = 0.3
        self.hit_threshold = 0
    
    def detect_people(self, frame, hit_threshold=0, use_nms=True, nms_threshold=0.4):
        """Обнаружение людей"""
        if frame is None:
            return []
        
        try:
            if self.use_yolo:
                return self._detect_with_yolo(frame, use_nms, nms_threshold)
            else:
                return self._detect_with_hog(frame, hit_threshold, use_nms, nms_threshold)
                
        except Exception as e:
            self.detection_error.emit(f"Ошибка обнаружения: {str(e)}")
            return []
    
    def _detect_with_yolo(self, frame, use_nms=True, nms_threshold=0.4):
        """Обнаружение с помощью YOLO"""
        if not self.model_loaded:
            try:
                self.yolo_model = YOLO('yolov8n.pt')
                self.model_loaded = True
                print("YOLO модель загружена")
            except Exception as e:
                print(f"Ошибка загрузки YOLO: {e}")
                self.use_yolo = False
                return self._detect_with_hog(frame, 0, use_nms, nms_threshold)
        # Изменяем размер для YOLO (оптимально 640x640)
        height, width = frame.shape[:2]
        
        # Запускаем детекцию (класс 0 = person)
        results = self.yolo_model(frame, conf=self.confidence_threshold, classes=[0], verbose=False)
        
        detections = []
        
        for result in results:
            if result.boxes is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                
                for box, conf in zip(boxes, confidences):
                    x1, y1, x2, y2 = map(int, box)
                    w = x2 - x1
                    h = y2 - y1
                    
                    # Фильтруем по размеру (слишком маленькие игнорируем)
                    if w > 20 and h > 40:
                        detections.append((x1, y1, w, h))
                        print(f"[YOLO] Обнаружен человек, уверенность: {conf:.2f}")
        
        # Убираем дубликаты
        if use_nms and detections:
            detections = self.non_max_suppression(detections, nms_threshold)
        
        if detections:
            self.person_detected.emit(detections)
        
        return detections
    
    def _detect_with_hog(self, frame, hit_threshold=0, use_nms=True, nms_threshold=0.4):
        """Обнаружение с помощью HOG (запасной вариант)"""
        all_rects = []
        
        # Улучшаем контрастность
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        l = clahe.apply(l)
        enhanced = cv2.merge((l, a, b))
        enhanced = cv2.cvtColor(enhanced, cv2.COLOR_LAB2BGR)
        
        gray = cv2.cvtColor(enhanced, cv2.COLOR_BGR2GRAY)
        
        # Поиск лиц (для обнаружения частично скрытых людей)
        faces = self.face_cascade.detectMultiScale(
            gray, scaleFactor=1.05, minNeighbors=3, minSize=(40, 40)
        )
        for (x, y, w, h) in faces:
            body_w = int(w * 2.5)
            body_h = int(h * 3.5)
            body_x = max(0, x - w // 2)
            body_y = max(0, y - h // 2)
            all_rects.append((body_x, body_y, body_w, body_h))
        
        # HOG детекция с разными порогами
        for threshold in [-0.5, 0, 0.3]:  # Разные пороги для лучшего обнаружения
            rects, weights = self.hog.detectMultiScale(
                enhanced,
                winStride=self.win_stride,
                padding=self.padding,
                scale=self.scale,
                hitThreshold=threshold
            )
            
            # Фильтруем по уверенности
            for i, rect in enumerate(rects):
                if i < len(weights) and weights[i] > 0.2:
                    all_rects.append(rect)
        
        # Убираем дубликаты
        if use_nms and all_rects:
            all_rects = self.non_max_suppression(all_rects, nms_threshold)
        
        # Фильтруем по размеру
        all_rects = [r for r in all_rects if r[2] > 30 and r[3] > 60]
        
        if all_rects:
            self.person_detected.emit(all_rects)
            print(f"[HOG] Обнаружено {len(all_rects)} человек(а)")
        
        return all_rects
    
    def non_max_suppression(self, rects: List[Tuple[int, int, int, int]], 
                           threshold: float = 0.4) -> List[Tuple[int, int, int, int]]:
        """Подавление не-максимумов"""
        if len(rects) == 0:
            return []
        
        # Конвертируем в формат (x1, y1, x2, y2)
        boxes = [(x, y, x + w, y + h) for x, y, w, h in rects]
        
        # Сортируем по площади
        areas = [(x2 - x1) * (y2 - y1) for (x1, y1, x2, y2) in boxes]
        indices = np.argsort(areas)[::-1]
        
        filtered_boxes = []
        
        while len(indices) > 0:
            current = indices[0]
            filtered_boxes.append(boxes[current])
            
            remaining_indices = []
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
                
                if union > 0 and intersection / union < threshold:
                    remaining_indices.append(idx)
            
            indices = np.array(remaining_indices)
        
        return [(x1, y1, x2 - x1, y2 - y1) for (x1, y1, x2, y2) in filtered_boxes]
    
    def draw_detections(self, frame, detections: List[Tuple[int, int, int, int]], 
                       color: Tuple[int, int, int] = (0, 255, 0),
                       thickness: int = 2) -> np.ndarray:
        """Рисует рамки вокруг обнаруженных людей"""
        if frame is None or len(detections) == 0:
            return frame
        
        result = frame.copy()
        
        for i, (x, y, w, h) in enumerate(detections):
            # Рисуем рамку
            cv2.rectangle(result, (x, y), (x + w, y + h), color, thickness)
            
            # Добавляем подпись
            label = f"Person {i+1}"
            (text_w, text_h), _ = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.5, 2)
            cv2.rectangle(result, (x, y - text_h - 5), (x + text_w, y), color, -1)
            cv2.putText(result, label, (x, y - 5),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 2)
        
        return result
    
    def get_detection_statistics(self, detections: List[Tuple[int, int, int, int]], 
                                frame_shape: Tuple[int, int]) -> dict:
        """Получает статистику об обнаруженных людях"""
        stats = {
            "total_people": len(detections),
            "positions": [],
            "areas": [],
            "frame_size": frame_shape
        }
        
        height, width = frame_shape
        
        for x, y, w, h in detections:
            center_x = x + w // 2
            center_y = y + h // 2
            
            # Определяем позицию
            if center_x < width // 3:
                h_pos = "слева"
            elif center_x > 2 * width // 3:
                h_pos = "справа"
            else:
                h_pos = "в центре"
            
            if center_y < height // 3:
                v_pos = "вверху"
            elif center_y > 2 * height // 3:
                v_pos = "внизу"
            else:
                v_pos = "в середине"
            
            stats["positions"].append(f"{v_pos} {h_pos}")
            stats["areas"].append(w * h)
        
        return stats


class DetectionThread(QThread):
    """Поток для асинхронного обнаружения людей"""
    
    detection_ready = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.detector = PersonDetector()
        self.frame = None
        self.threshold = 0.3
        self._is_running = True
    
    def set_frame(self, frame, threshold=0.3):
        """Устанавливает кадр для обработки"""
        self.frame = frame
        self.threshold = threshold
    
    def run(self):
        """Запуск обработки в потоке"""
        if self.frame is not None:
            detections = self.detector.detect_people(
                self.frame, 
                hit_threshold=self.threshold
            )
            if detections:
                self.detection_ready.emit(detections)
    
    def stop(self):
        """Останавливает поток"""
        self._is_running = False
        self.quit()
        self.wait()