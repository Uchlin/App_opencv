from PyQt6.QtCore import QThread, pyqtSignal
import numpy as np
from fire_detector import FireDetector

class FireDetectionThread(QThread):
    """Поток для асинхронного обнаружения возгораний"""
    
    fire_detection_ready = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.detector = FireDetector()  # Без параметра use_yolo
        self.frame = None
        self.detect_smoke = True
        self.use_motion = False
        self._is_running = True
    
    def set_frame(self, frame: np.ndarray, detect_smoke: bool = True, use_motion: bool = False):
        """Устанавливает кадр для обработки"""
        self.frame = frame
        self.detect_smoke = detect_smoke
        self.use_motion = use_motion
    
    def run(self):
        """Запуск обработки в потоке"""
        if self.frame is not None:
            detections = self.detector.detect_fire(
                self.frame,
                detect_smoke=self.detect_smoke,
                use_motion=self.use_motion
            )
            if detections:
                self.fire_detection_ready.emit(detections)
    
    def stop(self):
        """Останавливает поток"""
        self._is_running = False
        self.quit()
        self.wait()