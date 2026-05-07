from PyQt6.QtWidgets import QWidget, QFrame, QPushButton, QHBoxLayout, QFileDialog
from PyQt6.QtCore import Qt, pyqtSignal, QPoint
from .dropdown_menu import DropdownMenu

class HeaderWidget(QWidget):
    # Сигналы для кнопок
    button1_clicked = pyqtSignal(str)
    button2_clicked = pyqtSignal(str)
    button3_clicked = pyqtSignal(str)
    button4_clicked = pyqtSignal(str)
    clear_clicked = pyqtSignal()
    file_opened = pyqtSignal(str)  # Новый сигнал для открытого файла
    
    def __init__(self):
        super().__init__()
        self.dropdowns = {}
        self.initUI()
    
    def initUI(self):
        self.setFixedHeight(30)
        
        # Создаем полосу
        border_height = 30
        self.separator = QFrame(self)
        self.separator.setFrameShape(QFrame.Shape.HLine)
        self.separator.setStyleSheet(f"""
            background-color: white; 
            max-height: {border_height}px; 
            min-height: {border_height}px;
            border: none;
            border-bottom: 40px solid lightgrey;
        """)
        
        # Создаем горизонтальный layout для кнопок
        button_layout = QHBoxLayout(self)
        button_layout.setSpacing(0)
        button_layout.setContentsMargins(0, 0, 0, 0)
        
        # Создаем кнопки
        self.btn1 = QPushButton("Файл")
        self.btn2 = QPushButton("Правка")
        self.btn3 = QPushButton("Вид")
        self.btn4 = QPushButton("Справка")
        self.btn5 = QPushButton("Очистить")
        
        # Создаем выпадающие меню
        menu1 = DropdownMenu(["Открыть файл...", "Сохранить", "Выход"], self)
        menu1.item_clicked.connect(lambda text: self.on_menu_item_clicked(self.btn1, text))
        self.dropdowns[self.btn1] = menu1
        
        menu2 = DropdownMenu(["Копировать", "Вырезать", "Вставить", "Отменить"], self)
        menu2.item_clicked.connect(lambda text: self.on_menu_item_clicked(self.btn2, text))
        self.dropdowns[self.btn2] = menu2
        
        menu3 = DropdownMenu(["Увеличить", "Уменьшить", "Сбросить масштаб"], self)
        menu3.item_clicked.connect(lambda text: self.on_menu_item_clicked(self.btn3, text))
        self.dropdowns[self.btn3] = menu3
        
        menu4 = DropdownMenu(["О программе", "Помощь", "Обновления"], self)
        menu4.item_clicked.connect(lambda text: self.on_menu_item_clicked(self.btn4, text))
        self.dropdowns[self.btn4] = menu4
        
        # Подключаем сигналы кнопок
        self.btn1.clicked.connect(lambda: self.toggle_dropdown(self.btn1))
        self.btn2.clicked.connect(lambda: self.toggle_dropdown(self.btn2))
        self.btn3.clicked.connect(lambda: self.toggle_dropdown(self.btn3))
        self.btn4.clicked.connect(lambda: self.toggle_dropdown(self.btn4))
        self.btn5.clicked.connect(self.clear_clicked.emit)
        
        # Добавляем кнопки в layout
        button_layout.addWidget(self.btn1)
        button_layout.addWidget(self.btn2)
        button_layout.addWidget(self.btn3)
        button_layout.addWidget(self.btn4)
        button_layout.addWidget(self.btn5)
        button_layout.addStretch()
        
        self.apply_styles()
        self.installEventFilter(self)
    
    def on_menu_item_clicked(self, button, item_text):
        """Обработчик клика по пункту меню"""
        # Закрываем выпадающее меню
        if button in self.dropdowns:
            self.dropdowns[button].hide()
        
        # Специальная обработка для "Открыть файл..."
        if button == self.btn1 and item_text == "Открыть файл...":
            self.open_file_dialog()
        else:
            # Для остальных пунктов отправляем сигнал
            if button == self.btn1:
                self.button1_clicked.emit(item_text)
            elif button == self.btn2:
                self.button2_clicked.emit(item_text)
            elif button == self.btn3:
                self.button3_clicked.emit(item_text)
            elif button == self.btn4:
                self.button4_clicked.emit(item_text)
    
    def open_file_dialog(self):
        """Открывает диалог выбора файла"""
        file_path, _ = QFileDialog.getOpenFileName(
            self,
            "Выберите файл",
            "",
            "Все файлы (*.*);;Текстовые файлы (*.txt);;Python файлы (*.py)"
        )
        
        if file_path:
            self.file_opened.emit(file_path)
            # Также отправляем сигнал с информацией о файле
            self.button1_clicked.emit(f"Открыт файл: {file_path}")
    
    def apply_styles(self):
        self.setStyleSheet("""
            QPushButton {
                background-color: white;
                color: black;
                border: none;
                padding: 5px 10px;
                font-size: 14px;
            }
            QPushButton:hover {
                background-color: lightblue;
            }
            QPushButton:pressed {
                background-color: lightskyblue;
            }
        """)
    
    def toggle_dropdown(self, button):
        dropdown = self.dropdowns.get(button)
        if not dropdown:
            return
        
        if dropdown.isVisible():
            dropdown.hide()
            return
        
        for other_dropdown in self.dropdowns.values():
            if other_dropdown.isVisible():
                other_dropdown.hide()
        
        button_pos = button.mapToGlobal(QPoint(0, button.height()))
        dropdown.show_at_position(button_pos.x(), button_pos.y())
    
    def resizeEvent(self, event):
        border_height = 30
        self.separator.setGeometry(0, self.height() - border_height - 1, 
                                   self.width(), border_height)
        super().resizeEvent(event)
    
    def eventFilter(self, obj, event):
        if event.type() == event.Type.MouseButtonPress:
            for dropdown in self.dropdowns.values():
                if dropdown.isVisible():
                    pos = event.globalPosition().toPoint()
                    if not dropdown.geometry().contains(dropdown.mapFromGlobal(pos)):
                        clicked_button = None
                        for btn in self.dropdowns.keys():
                            if btn.geometry().contains(btn.mapFromGlobal(pos)):
                                clicked_button = btn
                                break
                        
                        if not clicked_button:
                            dropdown.hide()
        return super().eventFilter(obj, event)