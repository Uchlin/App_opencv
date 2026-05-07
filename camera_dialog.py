from PyQt6.QtWidgets import QDialog, QVBoxLayout, QListWidget, QPushButton, QLabel, QHBoxLayout
from PyQt6.QtCore import Qt, QTimer
from PyQt6.QtGui import QImage, QPixmap
import cv2
import numpy as np
import sys

class CameraDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.cameras = []
        self.selected_camera = None
        self.preview_timer = QTimer()
        self.cap = None
        self.initUI()
        self.scan_cameras()
        
    def initUI(self):
        self.setWindowTitle("Выбор камеры")
        self.setModal(True)
        self.setMinimumSize(600, 400)
        
        layout = QVBoxLayout()
        
        # Список камер
        self.camera_list = QListWidget()
        self.camera_list.itemClicked.connect(self.on_camera_selected)
        layout.addWidget(QLabel("Доступные камеры:"))
        layout.addWidget(self.camera_list)
        
        # Область предпросмотра
        self.preview_label = QLabel()
        self.preview_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.preview_label.setMinimumHeight(300)
        self.preview_label.setStyleSheet("""
            QLabel {
                background-color: black;
                border: 1px solid #ccc;
                margin-top: 10px;
            }
        """)
        layout.addWidget(self.preview_label)
        
        # Статус
        self.status_label = QLabel("")
        self.status_label.setStyleSheet("color: gray;")
        layout.addWidget(self.status_label)
        
        # Кнопки
        button_layout = QHBoxLayout()
        self.connect_btn = QPushButton("Подключиться")
        self.connect_btn.setEnabled(False)
        self.connect_btn.clicked.connect(self.accept)
        
        refresh_btn = QPushButton("Обновить")
        refresh_btn.clicked.connect(self.scan_cameras)
        
        cancel_btn = QPushButton("Отмена")
        cancel_btn.clicked.connect(self.reject)
        
        button_layout.addStretch()
        button_layout.addWidget(refresh_btn)
        button_layout.addWidget(self.connect_btn)
        button_layout.addWidget(cancel_btn)
        
        layout.addLayout(button_layout)
        self.setLayout(layout)
    
    def scan_cameras(self):
        """Сканирует доступные камеры"""
        self.camera_list.clear()
        self.cameras = []
        self.status_label.setText("Поиск камер...")
        
        # Останавливаем предпросмотр
        self.stop_preview()
        
        # Проверяем первые 5 индексов камер (обычно достаточно)
        for i in range(5):
            try:
                # Для Windows используем CAP_DSHOW для более быстрого открытия
                if sys.platform == "win32":
                    cap = cv2.VideoCapture(i, cv2.CAP_DSHOW)
                else:
                    cap = cv2.VideoCapture(i)
                
                if cap.isOpened():
                    # Пробуем захватить один кадр для проверки
                    ret, frame = cap.read()
                    if ret:
                        camera_name = f"Камера {i}"
                        
                        # Пробуем получить разрешение
                        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
                        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
                        if width > 0 and height > 0:
                            camera_name = f"Камера {i} ({width}x{height})"
                        
                        self.cameras.append({
                            'id': i,
                            'name': camera_name,
                            'cap': cap
                        })
                        self.camera_list.addItem(camera_name)
                    else:
                        cap.release()
                else:
                    if cap:
                        cap.release()
            except Exception as e:
                print(f"Ошибка при проверке камеры {i}: {e}")
        
        if self.cameras:
            self.camera_list.setCurrentRow(0)
            self.on_camera_selected(self.camera_list.item(0))
            self.status_label.setText(f"Найдено камер: {len(self.cameras)}")
        else:
            self.preview_label.setText("📷 Камеры не найдены\n\nПроверьте подключение веб-камеры")
            self.connect_btn.setEnabled(False)
            self.status_label.setText("Камеры не найдены")
    
    def on_camera_selected(self, item):
        """При выборе камеры из списка"""
        index = self.camera_list.row(item)
        if 0 <= index < len(self.cameras):
            self.selected_camera = self.cameras[index]['id']
            self.connect_btn.setEnabled(True)
            self.start_preview()
    
    def start_preview(self):
        """Запускает предпросмотр с выбранной камеры"""
        # Останавливаем предыдущий предпросмотр
        self.stop_preview()
        
        if self.selected_camera is not None:
            try:
                # Открываем камеру для предпросмотра
                if sys.platform == "win32":
                    self.cap = cv2.VideoCapture(self.selected_camera, cv2.CAP_DSHOW)
                else:
                    self.cap = cv2.VideoCapture(self.selected_camera)
                
                if self.cap.isOpened():
                    # Устанавливаем небольшое разрешение для предпросмотра
                    self.cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
                    self.cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
                    
                    self.preview_timer.timeout.connect(self.update_preview)
                    self.preview_timer.start(33)  # ~30 FPS
                else:
                    self.preview_label.setText("Не удалось открыть камеру для предпросмотра")
            except Exception as e:
                self.preview_label.setText(f"Ошибка: {str(e)}")
    
    def update_preview(self):
        """Обновляет кадр предпросмотра"""
        if self.cap and self.cap.isOpened():
            ret, frame = self.cap.read()
            if ret:
                # Конвертируем BGR в RGB
                frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                
                # Изменяем размер для отображения
                h, w = frame_rgb.shape[:2]
                max_height = 300
                if h > max_height:
                    scale = max_height / h
                    new_w = int(w * scale)
                    frame_rgb = cv2.resize(frame_rgb, (new_w, max_height))
                
                # Конвертируем в QImage
                h, w, ch = frame_rgb.shape
                bytes_per_line = ch * w
                qt_image = QImage(frame_rgb.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
                
                # Отображаем
                pixmap = QPixmap.fromImage(qt_image)
                self.preview_label.setPixmap(pixmap)
    
    def stop_preview(self):
        """Останавливает предпросмотр"""
        if self.preview_timer.isActive():
            self.preview_timer.stop()
            try:
                self.preview_timer.timeout.disconnect()
            except:
                pass
        
        if self.cap:
            self.cap.release()
            self.cap = None
    
    def get_selected_camera(self):
        """Возвращает ID выбранной камеры"""
        return self.selected_camera
    
    def reject(self):
        """Закрытие диалога"""
        self.stop_preview()
        super().reject()
    
    def accept(self):
        """Подтверждение выбора"""
        self.stop_preview()
        super().accept()
    
    def closeEvent(self, event):
        """При закрытии окна"""
        self.stop_preview()
        event.accept()