import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from typing import List, Tuple, Dict
import os

try:
    from ultralytics import YOLO
    YOLO_AVAILABLE = True
except ImportError:
    YOLO_AVAILABLE = False
    print("YOLO не установлен. Установите: pip install ultralytics")

class ShelfDetector(QObject):
    """Класс для обнаружения ячеек стеллажа с использованием YOLO"""
    
    detection_ready = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        
        self.use_yolo = YOLO_AVAILABLE
        self.model = None
        self.model_loaded = False
        
        # Параметры для YOLO
        self.confidence_threshold = 0.25
        self.iou_threshold = 0.45
        
        # Если YOLO не доступен, используем простую сетку
        self.rows = 3
        self.cols = 4
        
        # Загружаем модель
        self.load_model()
    
    def load_model(self):
        """Загружает YOLO модель"""
        if not self.use_yolo:
            print("YOLO не доступен, использую режим сетки")
            return
        
        try:
            # Пробуем загрузить кастомную модель для стеллажей
            # Если нет - используем стандартную
            model_paths = [
                "best.pt",  # Кастомная модель в папке проекта
                "shelf_detector.pt",
                "yolov8n.pt"  # Стандартная модель
            ]
            
            for path in model_paths:
                if os.path.exists(path):
                    self.model = YOLO(path)
                    print(f"Загружена модель: {path}")
                    break
            
            if self.model is None:
                # Скачиваем стандартную модель
                self.model = YOLO('yolov8n.pt')
                print("Загружена стандартная модель YOLOv8n")
            
            self.model_loaded = True
            
        except Exception as e:
            print(f"Ошибка загрузки модели: {e}")
            self.use_yolo = False
    
    def detect_shelves(self, frame) -> List[Dict]:
        """
        Обнаружение ячеек стеллажа
        """
        if frame is None:
            return []
        
        try:
            if self.use_yolo and self.model_loaded:
                return self._detect_with_yolo(frame)
            else:
                return self._detect_with_grid(frame)
                
        except Exception as e:
            print(f"Ошибка обнаружения: {e}")
            return self._detect_with_grid(frame)
    
    def _detect_with_yolo(self, frame) -> List[Dict]:
        """Обнаружение с помощью YOLO"""
        height, width = frame.shape[:2]
        
        # Запускаем детекцию
        results = self.model(frame, conf=self.confidence_threshold, iou=self.iou_threshold, verbose=False)
        
        cells = []
        cell_id = 1
        
        for result in results:
            if result.boxes is not None:
                boxes = result.boxes.xyxy.cpu().numpy()
                classes = result.boxes.cls.cpu().numpy()
                confidences = result.boxes.conf.cpu().numpy()
                
                for box, cls, conf in zip(boxes, classes, confidences):
                    x1, y1, x2, y2 = map(int, box)
                    w = x2 - x1
                    h = y2 - y1
                    
                    # Фильтруем по размеру
                    if w > 30 and h > 30:
                        # Определяем статус ячейки
                        cell_roi = frame[y1:y2, x1:x2]
                        status = self.check_cell_status(cell_roi)
                        
                        cells.append({
                            "id": str(cell_id),
                            "status": status,
                            "bbox": (x1, y1, w, h),
                            "confidence": float(conf)
                        })
                        cell_id += 1
        
        # Сортируем ячейки
        cells.sort(key=lambda c: (c["bbox"][1], c["bbox"][0]))
        
        if cells:
            self.detection_ready.emit(cells)
            print(f"[YOLO] Обнаружено {len(cells)} ячеек")
        
        return cells
    
    def _detect_with_grid(self, frame) -> List[Dict]:
        """Обнаружение с помощью сетки (запасной вариант)"""
        height, width = frame.shape[:2]
        
        # Область стеллажа (можно настроить)
        shelf_x = int(width * 0.1)
        shelf_y = int(height * 0.15)
        shelf_w = int(width * 0.8)
        shelf_h = int(height * 0.7)
        
        cell_w = shelf_w // self.cols
        cell_h = shelf_h // self.rows
        
        cells = []
        
        for row in range(self.rows):
            for col in range(self.cols):
                x = shelf_x + col * cell_w
                y = shelf_y + row * cell_h
                w = cell_w
                h = cell_h
                
                cell_roi = frame[y:y+h, x:x+w]
                
                if cell_roi.size > 0:
                    status = self.check_cell_status(cell_roi)
                    
                    cells.append({
                        "id": f"{row+1}-{col+1}",
                        "status": status,
                        "bbox": (x, y, w, h)
                    })
        
        if cells:
            self.detection_ready.emit(cells)
            print(f"[GRID] Создано {len(cells)} ячеек сетки")
        
        return cells
    
    def check_cell_status(self, cell_roi) -> str:
        """Проверяет статус ячейки (занято/свободно)"""
        if cell_roi is None or cell_roi.size == 0:
            return "свободно"
        
        h, w = cell_roi.shape[:2]
        
        # Анализируем центральную область
        center_y = h // 2
        center_x = w // 2
        crop_size = min(h, w) // 3
        y1 = max(0, center_y - crop_size)
        y2 = min(h, center_y + crop_size)
        x1 = max(0, center_x - crop_size)
        x2 = min(w, center_x + crop_size)
        
        center_part = cell_roi[y1:y2, x1:x2]
        
        if center_part.size == 0:
            return "свободно"
        
        # Анализ текстуры и краев
        gray = cv2.cvtColor(center_part, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Анализ цвета
        hsv = cv2.cvtColor(center_part, cv2.COLOR_BGR2HSV)
        saturation = np.mean(hsv[:, :, 1])
        
        # Анализ яркости
        brightness = np.mean(gray)
        
        # Комбинированная оценка
        if edge_density > 0.03 or saturation > 80 or brightness < 100:
            return "занято"
        else:
            return "свободно"
    
    def draw_shelves(self, frame, cells: List[Dict]) -> np.ndarray:
        """Рисует рамки вокруг ячеек"""
        if frame is None or not cells:
            return frame
        
        result = frame.copy()
        
        for cell in cells:
            x, y, w, h = cell["bbox"]
            status = cell["status"]
            cell_id = cell["id"]
            
            # Цвет рамки
            if status == "занято":
                color = (0, 0, 255)  # Красный
            else:
                color = (0, 255, 0)  # Зеленый
            
            # Рисуем рамку
            cv2.rectangle(result, (x, y), (x + w, y + h), color, 2)
            
            # Номер ячейки
            cv2.putText(result, cell_id, (x + 5, y + 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)
            
            # Статус
            if status == "занято":
                cv2.putText(result, "●", (x + w - 15, y + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 0, 255), 2)
            else:
                cv2.putText(result, "○", (x + w - 15, y + 25),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
        
        return result
    
    def update_grid_size(self, rows, cols):
        """Обновляет размер сетки"""
        self.rows = rows
        self.cols = cols
        print(f"[SHELF] Сетка обновлена: {rows}x{cols}")
    
    def set_confidence(self, confidence):
        """Устанавливает порог уверенности"""
        self.confidence_threshold = confidence


class ShelfDetectionThread(QThread):
    """Поток для обнаружения ячеек стеллажа"""
    
    detection_ready = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.detector = ShelfDetector()
        self.frame = None
        self.running = True
        self.scale = 0.5
    
    def set_frame(self, frame):
        """Устанавливает кадр для обработки"""
        if self.scale != 1.0:
            h, w = frame.shape[:2]
            new_w = int(w * self.scale)
            new_h = int(h * self.scale)
            self.frame = cv2.resize(frame, (new_w, new_h))
            self.scale_x = w / new_w if new_w > 0 else 1.0
            self.scale_y = h / new_h if new_h > 0 else 1.0
        else:
            self.frame = frame
            self.scale_x = 1.0
            self.scale_y = 1.0
    
    def run(self):
        if self.frame is not None:
            cells = self.detector.detect_shelves(self.frame)
            if cells:
                if self.scale_x != 1.0 or self.scale_y != 1.0:
                    for cell in cells:
                        x, y, w, h = cell["bbox"]
                        cell["bbox"] = (int(x * self.scale_x), 
                                       int(y * self.scale_y),
                                       int(w * self.scale_x), 
                                       int(h * self.scale_y))
                self.detection_ready.emit(cells)
    
    def stop(self):
        self.running = False
        self.quit()
        self.wait()