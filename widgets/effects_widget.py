# widgets/effects_widget.py
from PyQt6.QtWidgets import QFrame, QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QSlider, QHBoxLayout
from PyQt6.QtCore import Qt, pyqtSignal

class EffectsWidget(QWidget):
    """Виджет для выбора и настройки эффектов"""
    
    effect_applied = pyqtSignal(str, dict)  # Сигнал для применения эффекта (название, параметры)
    effect_reset = pyqtSignal()  # Сигнал для сброса эффектов
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setup_ui()
        self.apply_styles()
    def setup_ui(self):
        """Создаёт интерфейс виджета эффектов"""
        layout = QVBoxLayout()
        layout.setContentsMargins(10, 10, 0, 10)
        
        # Заголовок
        title_label = QLabel("Эффекты")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(title_label)
        
        # Создаем кнопку-заголовок для сворачивания
        header_btn = QPushButton()
        header_btn.setCheckable(True)
        header_btn.setChecked(False)
        header_btn.setFlat(True)
        header_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                font-weight: bold;
                padding: 8px;
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton:checked {
                background-color: #e5e5e5;
            }
        """)
        
        # Создаем layout для кнопки
        btn_layout = QHBoxLayout(header_btn)
        btn_layout.setContentsMargins(10, 5, 10, 5)
        
        # Текст слева
        title_text = QLabel("Цветовые настройки")
        title_text.setStyleSheet("background-color: transparent; font-weight: bold;")
        
        # Стрелка справа (создаем как QLabel)
        self.arrow_label = QLabel("◿")
        self.arrow_label.setStyleSheet("background-color: transparent; font-weight: bold; font-size: 14px;")
        
        btn_layout.addWidget(title_text)
        btn_layout.addStretch()  # Растяжка, чтобы стрелка была справа
        btn_layout.addWidget(self.arrow_label)
        
        # Контейнер для содержимого
        content_frame = QFrame()
        content_frame.setVisible(False)  # Изначально свернуто
        
        content_layout = QVBoxLayout(content_frame)
        content_layout.setContentsMargins(10, 10, 0, 10)
        content_layout.setSpacing(8)
        
        # Яркость (в одной строке)
        brightness_layout = QHBoxLayout()
        brightness_label = QLabel("Яркость:")
        brightness_label.setFixedWidth(80)
        self.brightness_slider = QSlider(Qt.Orientation.Horizontal)
        self.brightness_slider.setRange(-100, 100)
        self.brightness_slider.setValue(0)
        self.brightness_value_label = QLabel("0")
        self.brightness_value_label.setFixedWidth(25)
        self.brightness_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)

        brightness_layout.addWidget(brightness_label)
        brightness_layout.addWidget(self.brightness_slider, 1)
        brightness_layout.addWidget(self.brightness_value_label)
        content_layout.addLayout(brightness_layout)
        
        # Контрастность (в одной строке)
        contrast_layout = QHBoxLayout()
        contrast_label = QLabel("Контрастность:")
        contrast_label.setFixedWidth(80)
        self.contrast_slider = QSlider(Qt.Orientation.Horizontal)
        self.contrast_slider.setRange(-100, 100)
        self.contrast_slider.setValue(0)
        self.contrast_value_label = QLabel("0")
        self.contrast_value_label.setFixedWidth(25)
        self.contrast_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        contrast_layout.addWidget(contrast_label)
        contrast_layout.addWidget(self.contrast_slider, 1)
        contrast_layout.addWidget(self.contrast_value_label)
        content_layout.addLayout(contrast_layout)
        
        # Резкость (в одной строке)
        sharpness_layout = QHBoxLayout()
        sharpness_label = QLabel("Резкость:")
        sharpness_label.setFixedWidth(80)
        self.sharpness_slider = QSlider(Qt.Orientation.Horizontal)
        self.sharpness_slider.setRange(0, 100)
        self.sharpness_slider.setValue(0)
        self.sharpness_value_label = QLabel("0")
        self.sharpness_value_label.setFixedWidth(25)
        self.sharpness_value_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        sharpness_layout.addWidget(sharpness_label)
        sharpness_layout.addWidget(self.sharpness_slider, 1)
        sharpness_layout.addWidget(self.sharpness_value_label)
        content_layout.addLayout(sharpness_layout)
        # Создаем второй заголовок для поиска человека
        person_header_btn = QPushButton()
        person_header_btn.setCheckable(True)
        person_header_btn.setChecked(False)
        person_header_btn.setFlat(True)
        person_header_btn.setStyleSheet("""
            QPushButton {
                text-align: left;
                font-weight: bold;
                padding: 8px;
                background-color: #f5f5f5;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 5px;
            }
            QPushButton:hover {
                background-color: #e5e5e5;
            }
            QPushButton:checked {
                background-color: #e5e5e5;
            }
        """)

        # Layout для второго заголовка
        person_btn_layout = QHBoxLayout(person_header_btn)
        person_btn_layout.setContentsMargins(10, 5, 10, 5)

        person_title_text = QLabel("Поиск человека")
        person_title_text.setStyleSheet("background-color: transparent; font-weight: bold;")

        self.person_arrow_label = QLabel("◿")
        self.person_arrow_label.setStyleSheet("background-color: transparent; font-weight: bold; font-size: 14px;")

        person_btn_layout.addWidget(person_title_text)
        person_btn_layout.addStretch()
        person_btn_layout.addWidget(self.person_arrow_label)

        # Контейнер для содержимого поиска человека
        person_content_frame = QFrame()
        person_content_frame.setVisible(False)

        person_content_layout = QVBoxLayout(person_content_frame)
        person_content_layout.setContentsMargins(10, 10, 0, 10)
        person_content_layout.setSpacing(8)

        # Кнопка включения/выключения поиска
        enable_detection_layout = QHBoxLayout()
        self.enable_detection_checkbox = QPushButton("Включить поиск")
        self.enable_detection_checkbox.setCheckable(True)
        self.enable_detection_checkbox.setStyleSheet("""
            QPushButton:checked {
                background-color: #4CAF50;
                color: white;
            }
        """)
        enable_detection_layout.addWidget(self.enable_detection_checkbox)
        person_content_layout.addLayout(enable_detection_layout)

        # Порог уверенности
        threshold_layout = QHBoxLayout()
        threshold_label = QLabel("Порог:")
        threshold_label.setFixedWidth(80)
        self.threshold_slider = QSlider(Qt.Orientation.Horizontal)
        self.threshold_slider.setRange(0, 100)
        self.threshold_slider.setValue(50)
        self.threshold_value_label = QLabel("0.5")
        self.threshold_value_label.setFixedWidth(35)

        threshold_layout.addWidget(threshold_label)
        threshold_layout.addWidget(self.threshold_slider, 1)
        threshold_layout.addWidget(self.threshold_value_label)
        person_content_layout.addLayout(threshold_layout)

        # Функция сворачивания для второго блока
        def toggle_person_content():
            is_checked = person_header_btn.isChecked()
            person_content_frame.setVisible(is_checked)
            if is_checked:
                self.person_arrow_label.setText("◹")
            else:
                self.person_arrow_label.setText("◿")

        person_header_btn.clicked.connect(toggle_person_content)

        # Добавляем в основной layout
        layout.addWidget(person_header_btn)
        layout.addWidget(person_content_frame)

        # Подключаем сигналы
        self.enable_detection_checkbox.clicked.connect(self.on_detection_toggled)
        self.threshold_slider.valueChanged.connect(self.on_threshold_changed)
        
        # Функция сворачивания/разворачивания
        def toggle_content():
            is_checked = header_btn.isChecked()
            content_frame.setVisible(is_checked)
            if is_checked:
                self.arrow_label.setText("◹")
            else:
                self.arrow_label.setText("◿")
        
        header_btn.clicked.connect(toggle_content)
        
        layout.addWidget(header_btn)
        layout.addWidget(content_frame)
        
        # Кнопка сброса (остается всегда видимой)
        reset_btn = QPushButton("Сбросить все эффекты")
        reset_btn.clicked.connect(self.reset_effects)
        layout.addWidget(reset_btn)
        
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Подключаем сигналы
        self.brightness_slider.valueChanged.connect(self.on_brightness_changed)
        self.contrast_slider.valueChanged.connect(self.on_contrast_changed)
        self.sharpness_slider.valueChanged.connect(self.on_sharpness_changed)
        
    def on_brightness_changed(self, value):
        """Обработчик изменения яркости"""
        self.brightness_value_label.setText(str(value))
        self.apply_effects()
        
    def on_contrast_changed(self, value):
        """Обработчик изменения контрастности"""
        self.contrast_value_label.setText(str(value))
        self.apply_effects()
        
    def on_sharpness_changed(self, value):
        """Обработчик изменения резкости"""
        self.sharpness_value_label.setText(str(value))
        self.apply_effects()
        
    def apply_effects(self):
        """Применяет текущие настройки яркости, контрастности и резкости"""
        brightness_value = self.brightness_slider.value()
        contrast_value = self.contrast_slider.value()
        sharpness_value = self.sharpness_slider.value()
        
        # Преобразуем контрастность из -100..100 в коэффициент 0.5..2.0
        alpha = 0.5 + (contrast_value + 100) / 200 * 1.5
        
        # Если все параметры равны 0, сбрасываем эффекты
        if brightness_value == 0 and contrast_value == 0 and sharpness_value == 0:
            self.effect_reset.emit()
            return
        
        # Отправляем один сигнал со всеми параметрами
        self.effect_applied.emit("all", {
            "brightness": brightness_value,
            "contrast": alpha,
            "sharpness": sharpness_value
        })
        
    def reset_effects(self):
        """Сбрасывает все эффекты"""
        self.brightness_slider.setValue(0)
        self.contrast_slider.setValue(0)
        self.sharpness_slider.setValue(0)
        self.effect_reset.emit()
        
    def on_detection_toggled(self, checked):
        """Включение/выключение поиска человека"""
        if checked:
            threshold = self.threshold_slider.value() / 100.0
            self.effect_applied.emit("detect_person", {"enabled": True, "threshold": threshold})
        else:
            self.effect_applied.emit("detect_person", {"enabled": False})

    def on_threshold_changed(self, value):
        """Изменение порога уверенности"""
        threshold = value / 100.0
        self.threshold_value_label.setText(f"{threshold:.1f}")
        if self.enable_detection_checkbox.isChecked():
            self.effect_applied.emit("detect_person", {"enabled": True, "threshold": threshold})
    def apply_styles(self):
        """Применяет стили для виджета"""
        self.setStyleSheet("""
            QGroupBox {
                font-weight: bold;
                border: 1px solid #ccc;
                border-radius: 5px;
                margin-top: 10px;
                padding-top: 10px;
            }
            QGroupBox::title {
                subcontrol-origin: margin;
                left: 10px;
                padding: 0 5px 0 5px;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 8px;
                font-size: 12px;
            }
            QPushButton:hover {
                background-color: #e0e0e0;
            }
            QSlider::groove:horizontal {
                height: 4px;
                background: #ddd;
                border-radius: 2px;
            }
            QSlider::handle:horizontal {
                background: #4CAF50;
                width: 14px;
                height: 14px;
                margin: -5px 0;
                border-radius: 7px;
            }
            QSlider::handle:horizontal:hover {
                background: #45a049;
            }
            QLabel {
                color: #333;
            }
        """)