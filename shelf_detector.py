"""
YOLO детектор для полок и ячеек
Использует обученную модель shelf_model.pt
"""

from ultralytics import YOLO
import cv2
import numpy as np
import os
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum

@dataclass
class ShelfCell:
    row: int
    col: int
    x: int
    y: int
    width: int
    height: int
    is_occupied: bool = False
    confidence: float = 0.0

@dataclass
class Shelf:
    shelf_id: int
    y_position: int
    height: int
    cells: List[ShelfCell]
    confidence: float = 0.0
    angle: float = 0.0

class DetectionMethod(Enum):
    YOLO = "yolo"
    MANUAL = "manual"

class YOLOShelfDetector:
    """Детектор полок и ячеек на основе обученной YOLO модели"""
    
    def __init__(self, model_path: str = 'shelf_model.pt', conf_threshold: float = 0.5):
        """
        Инициализация YOLO детектора
        
        Args:
            model_path: путь к обученной модели .pt
            conf_threshold: порог уверенности (0.5 = 50%)
        """
        self.model_path = model_path
        self.conf_threshold = conf_threshold
        self.model = None
        self._load_model()
        
    def _load_model(self):
        """Загрузка обученной модели YOLO"""
        if os.path.exists(self.model_path):
            from ultralytics import YOLO
            self.model = YOLO(self.model_path)
            print(f"✅ YOLO модель загружена: {self.model_path}")
        else:
            print(f"❌ Модель {self.model_path} не найдена!")
            raise FileNotFoundError(f"Модель не найдена: {self.model_path}")
    
    def set_confidence_threshold(self, threshold: float):
        """Установка порога уверенности"""
        self.conf_threshold = max(0.1, min(0.9, threshold))
    
    def detect_shelves(self, frame: np.ndarray, method: DetectionMethod = DetectionMethod.YOLO) -> Tuple[List[Shelf], List[ShelfCell]]:
        """
        Обнаружение полок и ячеек на кадре
        
        Args:
            frame: изображение в формате numpy (BGR)
            method: метод обнаружения (YOLO или MANUAL)
        
        Returns:
            tuple: (список полок, список ячеек)
        """
        if frame is None:
            return [], []
        
        if method == DetectionMethod.MANUAL:
            return self._detect_manual(frame)
        else:
            return self._detect_yolo(frame)
    
    def _detect_yolo(self, frame: np.ndarray) -> Tuple[List[Shelf], List[ShelfCell]]:
        """Обнаружение с помощью YOLO модели - возвращаем только ячейки"""
        if self.model is None:
            return [], []
        
        results = self.model(frame, conf=self.conf_threshold, verbose=False)
        
        cells = []
        
        if results[0].boxes is not None:
            for box in results[0].boxes:
                x1, y1, x2, y2 = map(int, box.xyxy[0].tolist())
                conf = box.conf[0].item()
                
                if (x2 - x1) > 30 and (y2 - y1) > 30:
                    cell = ShelfCell(
                        row=0,
                        col=len(cells),
                        x=x1,
                        y=y1,
                        width=x2 - x1,
                        height=y2 - y1,
                        confidence=conf
                    )
                    cells.append(cell)
        
        # Возвращаем пустой список полок и список ячеек
        return [], cells
    
    def _detect_manual(self, frame: np.ndarray) -> Tuple[List[Shelf], List[ShelfCell]]:
        """Ручное обнаружение (если нужно)"""
        height, width = frame.shape[:2]
        
        # Простой вариант - равномерная сетка
        shelves_count = 4
        cells_per_shelf = 6
        
        shelf_height = height // shelves_count
        cell_width = width // cells_per_shelf
        
        shelves = []
        cells = []
        
        for shelf_idx in range(shelves_count):
            y_pos = shelf_idx * shelf_height
            
            shelf = Shelf(
                shelf_id=shelf_idx,
                y_position=y_pos,
                height=shelf_height,
                cells=[],
                confidence=0.8,
                angle=0
            )
            
            for col in range(cells_per_shelf):
                x_pos = col * cell_width
                cell = ShelfCell(
                    row=shelf_idx,
                    col=col,
                    x=x_pos + 2,
                    y=y_pos + 2,
                    width=cell_width - 4,
                    height=shelf_height - 4,
                    confidence=0.7
                )
                cells.append(cell)
                shelf.cells.append(cell)
            
            shelves.append(shelf)
        
        return shelves, cells
    
    def draw_detections(self, frame: np.ndarray, 
                       shelves: List[Shelf] = None,
                       cells: List[ShelfCell] = None,
                       draw_shelves: bool = True,
                       draw_cells: bool = True,
                       draw_grid: bool = True) -> np.ndarray:
        """Рисование обнаружений на кадре"""
        result = frame.copy()
        
        if draw_shelves and shelves:
            for shelf in shelves:
                # Рисуем полку
                cv2.rectangle(result, 
                            (0, shelf.y_position),
                            (frame.shape[1], shelf.y_position + shelf.height),
                            (255, 100, 0), 2)
                
                label = f"Shelf {shelf.shelf_id} ({shelf.confidence:.2f})"
                cv2.putText(result, label, 
                           (10, shelf.y_position - 5),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 100, 0), 2)
        
        if draw_cells and cells:
            for cell in cells:
                color = (0, 255, 0) if not cell.is_occupied else (0, 0, 255)
                cv2.rectangle(result,
                            (cell.x, cell.y),
                            (cell.x + cell.width, cell.y + cell.height),
                            color, 2)
                
                label = f"{cell.row},{cell.col} ({cell.confidence:.2f})"
                cv2.putText(result, label,
                           (cell.x + 5, cell.y + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return result
    
    def get_cell_status(self, frame: np.ndarray, cells: List[ShelfCell]) -> List[ShelfCell]:
        """
        Определение занятости ячеек
        
        Args:
            frame: изображение
            cells: список ячеек
        
        Returns:
            список ячеек с заполненным полем is_occupied
        """
        if self.model is None or not cells:
            return cells
        
        for cell in cells:
            # Вырезаем область ячейки
            cell_img = frame[cell.y:cell.y + cell.height, cell.x:cell.x + cell.width]
            
            if cell_img.size == 0:
                cell.is_occupied = False
                continue
            
            # Детекция объектов внутри ячейки
            results = self.model(cell_img, conf=self.conf_threshold, verbose=False)
            
            if results[0].boxes and len(results[0].boxes) > 0:
                cell.is_occupied = True
            else:
                cell.is_occupied = False
        
        return cells