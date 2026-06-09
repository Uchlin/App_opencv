import cv2
import numpy as np
from PyQt6.QtCore import QObject, pyqtSignal, QThread
from typing import List, Tuple, Dict, Optional
from dataclasses import dataclass
from enum import Enum
import math

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
    CONTOUR = "contour"
    LINE = "line"
    GRID = "grid"
    HYBRID = "hybrid"
    MANUAL = "manual"  # Ручной режим

class ShelfDetector(QObject):
    shelves_detected = pyqtSignal(list)
    cells_detected = pyqtSignal(list)
    detection_error = pyqtSignal(str)
    
    def __init__(self):
        super().__init__()
        
        # Параметры обнаружения
        self.min_shelf_height = 30
        self.max_shelf_height = 150
        self.min_cell_width = 40
        self.max_cell_width = 250
        self.min_cell_height = 25
        self.max_cell_height = 140
        
        # Параметры для обнаружения линий
        self.hough_threshold = 100
        self.min_line_length = 100
        self.max_line_gap = 30
        self.angle_tolerance = 30
        
        # Параметры для коррекции перспективы
        self.enable_perspective_correction = True
        self.perspective_margin = 50
        
        # Ручные настройки
        self.manual_shelves_count = 0  # 0 = автоопределение
        self.manual_cells_per_shelf = 0  # 0 = автоопределение
        self.manual_shelf_height = 0  # 0 = авто
        self.manual_cell_width = 0  # 0 = авто
        
        self.detection_method = DetectionMethod.HYBRID
        
    def set_manual_settings(self, shelves_count: int = 0, cells_per_shelf: int = 0,
                           shelf_height: int = 0, cell_width: int = 0):
        """Устанавливает ручные настройки"""
        self.manual_shelves_count = shelves_count
        self.manual_cells_per_shelf = cells_per_shelf
        self.manual_shelf_height = shelf_height
        self.manual_cell_width = cell_width
        
    def detect_shelves(self, frame: np.ndarray, 
                      method: DetectionMethod = None) -> Tuple[List[Shelf], List[ShelfCell]]:
        if frame is None:
            return [], []
        
        if method is None:
            method = self.detection_method
            
        try:
            height, width = frame.shape[:2]
            
            # Если ручной режим или заданы ручные параметры
            if method == DetectionMethod.MANUAL or self.manual_shelves_count > 0:
                shelves, cells = self._detect_manual(frame)
            else:
                # Автоматическое обнаружение
                corrected_frame = frame
                transform_matrix = None
                
                if self.enable_perspective_correction:
                    corrected_frame, transform_matrix = self._correct_perspective(frame)
                
                processed = self._preprocess_frame(corrected_frame)
                
                if method == DetectionMethod.CONTOUR:
                    shelves, cells = self._detect_by_contours(processed, corrected_frame)
                elif method == DetectionMethod.LINE:
                    shelves, cells = self._detect_by_lines_angle(processed, corrected_frame)
                elif method == DetectionMethod.GRID:
                    shelves, cells = self._detect_by_grid(processed, corrected_frame)
                else:
                    shelves, cells = self._detect_hybrid(processed, corrected_frame)
                
                if transform_matrix is not None and shelves:
                    shelves, cells = self._inverse_transform_detections(
                        shelves, cells, transform_matrix, frame.shape
                    )
            
            # Фильтруем результаты
            shelves = self._filter_shelves(shelves, height)
            cells = self._filter_cells_by_shelves(cells, shelves)
            
            if shelves:
                self.shelves_detected.emit(shelves)
            if cells:
                self.cells_detected.emit(cells)
            
            return shelves, cells
            
        except Exception as e:
            self.detection_error.emit(f"Ошибка обнаружения полок: {str(e)}")
            return [], []
    
    def _detect_manual(self, frame: np.ndarray) -> Tuple[List[Shelf], List[ShelfCell]]:
        """Ручное обнаружение полок и ячеек"""
        height, width = frame.shape[:2]
        
        shelves_count = self.manual_shelves_count
        cells_per_shelf = self.manual_cells_per_shelf
        
        # Если не задано количество полок, пробуем определить автоматически
        if shelves_count == 0:
            processed = self._preprocess_frame(frame)
            shelves, _ = self._detect_by_lines_angle(processed, frame)
            shelves_count = len(shelves)
            if shelves_count == 0:
                shelves_count = 4
        
        # Если не задано количество ячеек, пробуем определить
        if cells_per_shelf == 0:
            shelf_height = height // shelves_count
            shelf_region = frame[:shelf_height, :]
            cells_per_shelf = self._estimate_cells_count(shelf_region)
        
        # Вычисляем равномерные отступы
        shelf_height = height // shelves_count
        cell_width = width // cells_per_shelf
        
        # Создаем полки и ячейки
        shelves = []
        cells = []
        
        for shelf_idx in range(shelves_count):
            y_pos = shelf_idx * shelf_height
            
            if y_pos + shelf_height > height:
                continue
            
            shelf = Shelf(
                shelf_id=shelf_idx,
                y_position=y_pos,
                height=shelf_height,
                cells=[],
                confidence=0.9,
                angle=0
            )
            
            for col in range(cells_per_shelf):
                x_pos = col * cell_width
                
                if x_pos + cell_width > width:
                    continue
                
                cell = ShelfCell(
                    row=shelf_idx,
                    col=col,
                    x=x_pos + 2,
                    y=y_pos + 2,
                    width=cell_width - 4,
                    height=shelf_height - 4,
                    confidence=0.85
                )
                cells.append(cell)
                shelf.cells.append(cell)
            
            shelves.append(shelf)
        
        return shelves, cells
    
    def _correct_perspective(self, frame: np.ndarray) -> Tuple[np.ndarray, Optional[np.ndarray]]:
        """Коррекция перспективы"""
        height, width = frame.shape[:2]
        
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        edges = cv2.Canny(gray, 50, 150)
        
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, self.hough_threshold,
                                minLineLength=self.min_line_length,
                                maxLineGap=self.max_line_gap)
        
        if lines is None or len(lines) < 3:
            return frame, None
        
        angles = []
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            if abs(angle) < 45:
                angles.append(angle)
        
        if not angles:
            return frame, None
        
        median_angle = np.median(angles)
        
        if abs(median_angle) < 5:
            return frame, None
        
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, -median_angle, 1.0)
        rotated = cv2.warpAffine(frame, rotation_matrix, (width, height))
        
        return rotated, rotation_matrix
    
    def _inverse_transform_detections(self, shelves: List[Shelf], cells: List[ShelfCell],
                                     transform_matrix: np.ndarray, original_shape: Tuple) -> Tuple[List[Shelf], List[ShelfCell]]:
        """Обратное преобразование координат"""
        if transform_matrix is None:
            return shelves, cells
        
        inv_matrix = cv2.invertAffineTransform(transform_matrix)
        
        for shelf in shelves:
            points = np.array([
                [0, shelf.y_position],
                [original_shape[1], shelf.y_position],
                [0, shelf.y_position + shelf.height],
                [original_shape[1], shelf.y_position + shelf.height]
            ], dtype=np.float32)
            
            transformed = cv2.transform(points.reshape(-1, 1, 2), inv_matrix).reshape(-1, 2)
            shelf.y_position = int(np.min(transformed[:, 1]))
            shelf.height = int(np.max(transformed[:, 1]) - shelf.y_position)
        
        for cell in cells:
            points = np.array([
                [cell.x, cell.y],
                [cell.x + cell.width, cell.y],
                [cell.x, cell.y + cell.height],
                [cell.x + cell.width, cell.y + cell.height]
            ], dtype=np.float32)
            
            transformed = cv2.transform(points.reshape(-1, 1, 2), inv_matrix).reshape(-1, 2)
            cell.x = int(np.min(transformed[:, 0]))
            cell.y = int(np.min(transformed[:, 1]))
            cell.width = int(np.max(transformed[:, 0]) - cell.x)
            cell.height = int(np.max(transformed[:, 1]) - cell.y)
        
        return shelves, cells
    
    def _preprocess_frame(self, frame: np.ndarray) -> np.ndarray:
        """Предобработка кадра"""
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        enhanced = clahe.apply(gray)
        
        blurred = cv2.GaussianBlur(enhanced, (5, 5), 0)
        
        binary = cv2.adaptiveThreshold(blurred, 255, 
                                       cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                                       cv2.THRESH_BINARY_INV, 15, 3)
        
        kernel = np.ones((5, 5), np.uint8)
        closed = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel)
        
        edges1 = cv2.Canny(closed, 30, 100)
        edges2 = cv2.Canny(closed, 50, 150)
        edges = cv2.addWeighted(edges1, 0.5, edges2, 0.5, 0)
        
        return edges
    
    def _detect_by_lines_angle(self, edges: np.ndarray, original: np.ndarray) -> Tuple[List[Shelf], List[ShelfCell]]:
        """Обнаружение линий с учетом угла"""
        height, width = edges.shape
        
        lines = cv2.HoughLinesP(edges, 1, np.pi/180, self.hough_threshold,
                                minLineLength=self.min_line_length,
                                maxLineGap=self.max_line_gap)
        
        if lines is None:
            return [], []
        
        horizontal_groups = []
        vertical_groups = []
        
        for line in lines:
            x1, y1, x2, y2 = line[0]
            angle = math.degrees(math.atan2(y2 - y1, x2 - x1))
            length = math.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            
            if length < self.min_line_length:
                continue
            
            if abs(angle) < self.angle_tolerance or abs(abs(angle) - 180) < self.angle_tolerance:
                y_center = (y1 + y2) // 2
                if length > width * 0.4:
                    horizontal_groups.append((y_center, angle, line[0]))
            
            elif abs(abs(angle) - 90) < self.angle_tolerance:
                x_center = (x1 + x2) // 2
                if length > height * 0.3:
                    vertical_groups.append((x_center, angle, line[0]))
        
        horizontal_lines = self._group_lines_with_angle(horizontal_groups, 25)
        vertical_lines = self._group_lines_with_angle(vertical_groups, 30)
        
        shelves = []
        for i, (y, angle, _) in enumerate(horizontal_lines):
            next_y = height
            for y2, _, _ in horizontal_lines:
                if y2 > y and y2 - y > self.min_shelf_height:
                    next_y = min(next_y, y2)
            
            shelf_height = min(next_y - y, self.max_shelf_height)
            
            if self.min_shelf_height <= shelf_height <= self.max_shelf_height:
                shelf = Shelf(
                    shelf_id=i,
                    y_position=y,
                    height=shelf_height,
                    cells=[],
                    confidence=0.7,
                    angle=angle
                )
                shelves.append(shelf)
        
        cells = []
        for shelf_idx, shelf in enumerate(shelves):
            shelf_vertical = []
            for x, angle, line in vertical_lines:
                if shelf.y_position < x < shelf.y_position + shelf.height:
                    shelf_vertical.append(x)
            
            boundaries = [0] + sorted(shelf_vertical) + [width]
            
            for col in range(len(boundaries) - 1):
                x1 = boundaries[col]
                x2 = boundaries[col + 1]
                cell_width = x2 - x1
                
                if self.min_cell_width <= cell_width <= self.max_cell_width:
                    cell = ShelfCell(
                        row=shelf_idx,
                        col=col,
                        x=x1,
                        y=shelf.y_position,
                        width=cell_width,
                        height=shelf.height,
                        confidence=0.6
                    )
                    cells.append(cell)
                    shelf.cells.append(cell)
        
        return shelves, cells
    
    def _group_lines_with_angle(self, lines: List[Tuple], max_gap: int) -> List[Tuple]:
        """Группировка линий"""
        if not lines:
            return []
        
        lines.sort(key=lambda x: x[0])
        
        grouped = []
        current_group = [lines[0]]
        
        for line in lines[1:]:
            if line[0] - current_group[-1][0] <= max_gap:
                current_group.append(line)
            else:
                avg_y = sum(l[0] for l in current_group) // len(current_group)
                avg_angle = sum(l[1] for l in current_group) / len(current_group)
                best_line = max(current_group, key=lambda l: 
                               math.sqrt((l[2][2] - l[2][0])**2 + (l[2][3] - l[2][1])**2))
                grouped.append((avg_y, avg_angle, best_line[2]))
                current_group = [line]
        
        if current_group:
            avg_y = sum(l[0] for l in current_group) // len(current_group)
            avg_angle = sum(l[1] for l in current_group) / len(current_group)
            best_line = max(current_group, key=lambda l: 
                           math.sqrt((l[2][2] - l[2][0])**2 + (l[2][3] - l[2][1])**2))
            grouped.append((avg_y, avg_angle, best_line[2]))
        
        return grouped
    
    def _detect_by_contours(self, edges: np.ndarray, original: np.ndarray) -> Tuple[List[Shelf], List[ShelfCell]]:
        """Обнаружение по контурам"""
        contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        shelves = []
        cells = []
        contours = sorted(contours, key=lambda c: cv2.boundingRect(c)[1])
        
        for contour in contours:
            peri = cv2.arcLength(contour, True)
            approx = cv2.approxPolyDP(contour, 0.02 * peri, True)
            x, y, w, h = cv2.boundingRect(contour)
            
            if (self.min_shelf_height <= h <= self.max_shelf_height and 
                w > self.min_line_length and len(approx) >= 4):
                
                area = cv2.contourArea(contour)
                rect_area = w * h
                
                if area / rect_area > 0.6:
                    shelf = Shelf(
                        shelf_id=len(shelves),
                        y_position=y,
                        height=h,
                        cells=[],
                        confidence=0.75,
                        angle=0
                    )
                    shelves.append(shelf)
                    
                    shelf_region = original[y:y+h, x:x+w]
                    if shelf_region.size > 0:
                        separators = self._find_vertical_separators_angle(shelf_region)
                        
                        boundaries = [0] + sorted(separators) + [w]
                        for col in range(len(boundaries) - 1):
                            x1 = boundaries[col]
                            x2 = boundaries[col + 1]
                            cell_width = x2 - x1
                            
                            if self.min_cell_width <= cell_width <= self.max_cell_width:
                                cell = ShelfCell(
                                    row=len(shelves)-1,
                                    col=col,
                                    x=x + x1,
                                    y=y,
                                    width=cell_width,
                                    height=h,
                                    confidence=0.7
                                )
                                cells.append(cell)
                                shelf.cells.append(cell)
        
        return shelves, cells
    
    def _find_vertical_separators_angle(self, region: np.ndarray) -> List[int]:
        """Поиск вертикальных разделителей"""
        if region.size == 0:
            return []
        
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_x = np.abs(sobel_x)
        
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, 10))
        vertical = cv2.morphologyEx(sobel_x, cv2.MORPH_OPEN, kernel)
        
        projection = np.sum(vertical, axis=0)
        threshold = np.max(projection) * 0.4
        separators = []
        
        for x in range(1, len(projection) - 1):
            if (projection[x] > threshold and 
                projection[x] > projection[x-1] and 
                projection[x] > projection[x+1] and
                projection[x] > np.mean(projection) * 2):
                separators.append(x)
        
        return self._group_lines(separators, 25)
    
    def _detect_by_grid(self, edges: np.ndarray, original: np.ndarray) -> Tuple[List[Shelf], List[ShelfCell]]:
        """Обнаружение как сетки"""
        height, width = original.shape[:2]
        
        horizontal_projection = np.sum(edges, axis=1)
        projection_threshold = np.max(horizontal_projection) * 0.3
        
        shelves = []
        in_shelf = False
        shelf_start = 0
        
        for y in range(height):
            if horizontal_projection[y] > projection_threshold and not in_shelf:
                shelf_start = y
                in_shelf = True
            elif horizontal_projection[y] <= projection_threshold and in_shelf:
                shelf_height = y - shelf_start
                if self.min_shelf_height <= shelf_height <= self.max_shelf_height:
                    shelf = Shelf(
                        shelf_id=len(shelves),
                        y_position=shelf_start,
                        height=shelf_height,
                        cells=[],
                        confidence=0.7,
                        angle=0
                    )
                    shelves.append(shelf)
                in_shelf = False
        
        cells = []
        for shelf in shelves:
            num_cells = min(8, max(3, width // 80))
            cell_width = width // num_cells
            
            for col in range(num_cells):
                cell_x = col * cell_width
                cell = ShelfCell(
                    row=shelf.shelf_id,
                    col=col,
                    x=cell_x + 5,
                    y=shelf.y_position + 5,
                    width=cell_width - 10,
                    height=shelf.height - 10,
                    confidence=0.65
                )
                cells.append(cell)
                shelf.cells.append(cell)
        
        return shelves, cells
    
    def _detect_hybrid(self, edges: np.ndarray, original: np.ndarray) -> Tuple[List[Shelf], List[ShelfCell]]:
        """Комбинированный метод"""
        shelves, cells = self._detect_by_lines_angle(edges, original)
        
        if len(shelves) == 0:
            shelves, cells = self._detect_by_contours(edges, original)
        
        if len(shelves) == 0:
            shelves, cells = self._detect_by_grid(edges, original)
        
        return shelves, cells
    
    def _estimate_cells_count(self, region: np.ndarray) -> int:
        """Оценивает количество ячеек на полке"""
        if region.size == 0:
            return 4
        
        gray = cv2.cvtColor(region, cv2.COLOR_BGR2GRAY)
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_x = np.abs(sobel_x)
        
        vertical_sum = np.sum(sobel_x, axis=0)
        peak_count = 0
        peak_threshold = np.max(vertical_sum) * 0.4
        
        for i in range(1, len(vertical_sum) - 1):
            if vertical_sum[i] > peak_threshold and \
               vertical_sum[i] > vertical_sum[i-1] and \
               vertical_sum[i] > vertical_sum[i+1]:
                peak_count += 1
        
        return max(2, min(peak_count + 1, 8))
    
    def _group_lines(self, lines: List[int], max_gap: int) -> List[int]:
        """Группировка линий"""
        if not lines:
            return []
        
        lines.sort()
        grouped = []
        current_group = [lines[0]]
        
        for line in lines[1:]:
            if line - current_group[-1] <= max_gap:
                current_group.append(line)
            else:
                grouped.append(sum(current_group) // len(current_group))
                current_group = [line]
        
        if current_group:
            grouped.append(sum(current_group) // len(current_group))
        
        return grouped
    
    def _filter_shelves(self, shelves: List[Shelf], frame_height: int) -> List[Shelf]:
        """Фильтрация полок"""
        if not shelves:
            return []
        
        unique_shelves = []
        for shelf in shelves:
            is_duplicate = False
            for existing in unique_shelves:
                if abs(shelf.y_position - existing.y_position) < 30:
                    is_duplicate = True
                    break
            if not is_duplicate:
                unique_shelves.append(shelf)
        
        unique_shelves.sort(key=lambda s: s.y_position)
        return unique_shelves[:8]
    
    def _filter_cells_by_shelves(self, cells: List[ShelfCell], shelves: List[Shelf]) -> List[ShelfCell]:
        """Фильтрация ячеек"""
        if not shelves or not cells:
            return []
        
        valid_cells = []
        for cell in cells:
            for shelf in shelves:
                if (abs(cell.y - shelf.y_position) < 20 and 
                    abs(cell.height - shelf.height) < 20):
                    valid_cells.append(cell)
                    break
        
        return valid_cells
    
    def draw_detections(self, frame: np.ndarray, 
                       shelves: List[Shelf] = None,
                       cells: List[ShelfCell] = None,
                       draw_shelves: bool = True,
                       draw_cells: bool = True,
                       draw_grid: bool = True) -> np.ndarray:
        """Рисование обнаружений"""
        result = frame.copy()
        
        if draw_shelves and shelves:
            for shelf in shelves:
                cv2.rectangle(result, 
                            (0, shelf.y_position),
                            (frame.shape[1], shelf.y_position + shelf.height),
                            (255, 100, 0), 2)
                
                label = f"Shelf {shelf.shelf_id}"
                if shelf.angle != 0:
                    label += f" ({shelf.angle:.1f}°)"
                
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
                
                label = f"{cell.row},{cell.col}"
                cv2.putText(result, label,
                           (cell.x + 5, cell.y + 20),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.4, color, 1)
        
        return result


class ShelfDetectionThread(QThread):
    detection_ready = pyqtSignal(list, list)
    
    def __init__(self):
        super().__init__()
        self.detector = ShelfDetector()
        self.frame = None
        self.method = DetectionMethod.HYBRID
        self._is_running = True
    
    def set_frame(self, frame: np.ndarray, method: DetectionMethod = None):
        self.frame = frame
        if method:
            self.method = method
    
    def set_manual_settings(self, shelves_count: int = 0, cells_per_shelf: int = 0,
                           shelf_height: int = 0, cell_width: int = 0):
        """Установка ручных настроек для детектора"""
        self.detector.set_manual_settings(shelves_count, cells_per_shelf, shelf_height, cell_width)
    
    def run(self):
        if self.frame is not None:
            shelves, cells = self.detector.detect_shelves(self.frame, self.method)
            if shelves or cells:
                self.detection_ready.emit(shelves, cells)
    
    def stop(self):
        self._is_running = False
        self.quit()
        self.wait()