# datetime_widget.py
from PyQt6.QtWidgets import QHBoxLayout, QWidget, QVBoxLayout, QLabel
from PyQt6.QtCore import QTimer, Qt
from PyQt6.QtGui import QFont
from datetime import datetime


class DateTimeWidget(QWidget):
    """Виджет для отображения текущей даты и времени"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        self.start_timer()
        
    def initUI(self):
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 5, 0, 0)
        
        # Создаём виджет с рамкой
        frame_widget = QWidget()
        frame_widget.setObjectName("frame_widget")
        frame_widget.setStyleSheet("""
            QWidget#frame_widget {
                background-color: white;
                border: 2px solid white;
                border-radius: 10px;
            }
        """)
        
        # Внутренний layout для рамки
        frame_layout = QVBoxLayout(frame_widget)
        frame_layout.setContentsMargins(0, 0, 0, 0)
        
        # Метка для времени
        self.time_label = QLabel("--:--:--")
        self.time_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.time_label.setFont(QFont("Arial", 24, QFont.Weight.Bold))
        self.time_label.setStyleSheet("color: #2c3e50; background-color: transparent;")
        frame_layout.addWidget(self.time_label)
        
        # Метки для даты и дня недели
        self.date_label = QLabel("--.--.----")
        self.weekday_label = QLabel("")
        
        for label in [self.date_label, self.weekday_label]:
            label.setAlignment(Qt.AlignmentFlag.AlignCenter)
            label.setFont(QFont("Arial", 14))
            label.setStyleSheet("color: black; background-color: transparent;")
        
        datetime_layout = QHBoxLayout()
        datetime_layout.addWidget(self.date_label)
        datetime_layout.addWidget(self.weekday_label)
        datetime_layout.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        frame_layout.addLayout(datetime_layout)
        layout.addWidget(frame_widget)
        self.setLayout(layout)
        self.setFixedHeight(60)
        
    def start_timer(self):
        self.timer = QTimer()
        self.timer.timeout.connect(self.update_datetime)
        self.timer.start(1000)
        self.update_datetime()
        
    def update_datetime(self):
        now = datetime.now()
        self.time_label.setText(now.strftime("%H:%M:%S"))
        self.date_label.setText(now.strftime("%d.%m.%Y"))
        
        weekdays = ["Понедельник", "Вторник", "Среда", "Четверг", 
                    "Пятница", "Воскресенье", "Воскресенье"]
        self.weekday_label.setText(weekdays[now.weekday()])
        
    def stop_timer(self):
        if hasattr(self, 'timer'):
            self.timer.stop()