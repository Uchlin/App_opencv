from PyQt6.QtCore import QThread, pyqtSignal
from person_detector import PersonDetector

class DetectionThread(QThread):
    detection_ready = pyqtSignal(list)
    
    def __init__(self):
        super().__init__()
        self.detector = PersonDetector()
        self.frame = None
        self.threshold = 0.5
        self.running = True
    
    def set_frame(self, frame, threshold=0.5):
        self.frame = frame
        self.threshold = threshold
    
    def run(self):
        if self.frame is not None:
            detections = self.detector.detect_people(
                self.frame, hit_threshold=self.threshold
            )
            if detections:
                self.detection_ready.emit(detections)
    
    def stop(self):
        self.running = False