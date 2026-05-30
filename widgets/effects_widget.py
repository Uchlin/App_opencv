# widgets/effects_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QLabel, QPushButton, QGroupBox, QSlider, QCheckBox
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
        layout.setContentsMargins(10, 10, 10, 10)
        
        # Заголовок
        title_label = QLabel("Эффекты")
        title_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        title_label.setStyleSheet("font-size: 16px; font-weight: bold; padding: 5px;")
        layout.addWidget(title_label)
        
        # Группа основных эффектов
        effects_group = QGroupBox("Основные эффекты")
        effects_layout = QVBoxLayout(effects_group)
        effects_layout.setSpacing(5)
        
        # Создаем чекбоксы для эффектов
        self.effects_checkboxes = {}
        effects = [
            ("Черно-белый", "grayscale"),
            ("Размытие", "blur"),
            ("Контур", "edge_detection"),
            ("Сепия", "sepia"),
            ("Негатив", "negative"),
            ("Повышение яркости", "brightness"),
            ("Повышение контраста", "contrast")
        ]
        
        for label, effect_name in effects:
            checkbox = QCheckBox(label)
            checkbox.stateChanged.connect(lambda state, e=effect_name: self.on_effect_changed(e, state))
            effects_layout.addWidget(checkbox)
            self.effects_checkboxes[effect_name] = checkbox
        
        layout.addWidget(effects_group)
        
        # Группа дополнительных настроек
        settings_group = QGroupBox("Настройки")
        settings_layout = QVBoxLayout(settings_group)
        
        # Слайдер интенсивности
        self.intensity_label = QLabel("Интенсивность: 50%")
        self.intensity_slider = QSlider(Qt.Orientation.Horizontal)
        self.intensity_slider.setRange(0, 100)
        self.intensity_slider.setValue(50)
        self.intensity_slider.valueChanged.connect(self.on_intensity_changed)
        self.intensity_slider.setEnabled(False)
        
        settings_layout.addWidget(self.intensity_label)
        settings_layout.addWidget(self.intensity_slider)
        
        # Чекбокс автообновления
        self.auto_update = QCheckBox("Автообновление")
        self.auto_update.setChecked(True)
        settings_layout.addWidget(self.auto_update)
        
        # Кнопка сброса
        reset_btn = QPushButton("Сбросить все эффекты")
        reset_btn.clicked.connect(self.reset_effects)
        settings_layout.addWidget(reset_btn)
        
        layout.addWidget(settings_group)
        layout.addStretch()
        
        self.setLayout(layout)
        
        # Текущий активный эффект
        self.current_effect = "none"
        
    def on_effect_changed(self, effect_name, state):
        """Обработчик изменения состояния чекбокса"""
        if state == 2:  # Qt.CheckState.Checked
            # Чекбокс включен - применяем эффект
            # Отключаем все другие чекбоксы
            for name, checkbox in self.effects_checkboxes.items():
                if name != effect_name:
                    checkbox.setChecked(False)
            
            self.current_effect = effect_name
            self.intensity_slider.setEnabled(True)
            self.apply_current_effect()
        else:
            # Чекбокс выключен - сбрасываем эффект
            # Проверяем, есть ли другие включенные чекбоксы
            any_checked = any(
                checkbox.isChecked() for checkbox in self.effects_checkboxes.values()
            )
            
            if not any_checked:
                # Нет других эффектов - сбрасываем всё
                self.current_effect = "none"
                self.intensity_slider.setEnabled(False)
                self.effect_reset.emit()
            else:
                # Есть другие эффекты - применяем первый включенный
                for name, checkbox in self.effects_checkboxes.items():
                    if checkbox.isChecked():
                        self.current_effect = name
                        self.apply_current_effect()
                        break
            
    def on_intensity_changed(self, value):
        """Обработчик изменения интенсивности"""
        self.intensity_label.setText(f"Интенсивность: {value}%")
        if self.auto_update.isChecked() and self.current_effect != "none":
            self.apply_current_effect()
            
    def apply_current_effect(self):
        """Применяет текущий эффект с параметрами"""
        if self.current_effect == "none":
            return
            
        params = {}
        intensity = self.intensity_slider.value() / 50.0  # Преобразуем 0-100 в 0-2
        
        # Настраиваем параметры для разных эффектов
        if self.current_effect == "blur":
            kernel = int(3 + intensity * 10)  # 3-13
            if kernel % 2 == 0:
                kernel += 1
            params = {"kernel_size": kernel}
        elif self.current_effect == "edge_detection":
            threshold = int(50 + intensity * 50)  # 50-100
            params = {"low_threshold": threshold, "high_threshold": threshold * 2}
        elif self.current_effect == "brightness":
            value = int(-50 + intensity * 100)  # -50 до 150
            params = {"value": value}
        elif self.current_effect == "contrast":
            alpha = 0.5 + intensity  # 0.5 до 2.5
            params = {"alpha": alpha}
            
        self.effect_applied.emit(self.current_effect, params)
        
    def reset_effects(self):
        """Сбрасывает все эффекты"""
        # Отключаем все чекбоксы
        for checkbox in self.effects_checkboxes.values():
            checkbox.setChecked(False)
        
        self.current_effect = "none"
        self.intensity_slider.setEnabled(False)
        self.intensity_slider.setValue(50)
        self.effect_reset.emit()
        
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
            QCheckBox {
                spacing: 8px;
                padding: 3px;
            }
            QCheckBox::indicator {
                width: 16px;
                height: 16px;
                border-radius: 3px;
                border: 1px solid #ccc;
                background-color: white;
            }
            QCheckBox::indicator:checked {
                background-color: #4CAF50;
                border-color: #4CAF50;
            }
            QCheckBox::indicator:hover {
                border-color: #999;
            }
            QPushButton {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 3px;
                padding: 5px;
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
                width: 12px;
                height: 12px;
                margin: -4px 0;
                border-radius: 6px;
            }
            QSlider::handle:horizontal:hover {
                background: #45a049;
            }
        """)