# table_widget.py
from PyQt6.QtWidgets import QWidget, QVBoxLayout, QTableWidget, QTableWidgetItem, QHeaderView, QLabel
from PyQt6.QtCore import Qt, pyqtSignal
from PyQt6.QtGui import QColor


class InfoTableWidget(QWidget):
    """Виджет с таблицей для отображения информации о видео/эффектах"""
    
    # Сигналы для взаимодействия с основным приложением
    row_selected = pyqtSignal(int, dict)  # номер строки, данные строки
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.initUI()
        
    def initUI(self):
        # Основной layout для виджета
        layout = QVBoxLayout()
        layout.setContentsMargins(5, 5, 5, 5)
        layout.setSpacing(5)
        
        # Контейнер для таблицы с общей строкой
        table_container = QWidget()
        table_layout = QVBoxLayout(table_container)
        table_layout.setContentsMargins(0, 0, 0, 0)
        table_layout.setSpacing(0)
        
        # Общая строка над таблицей
        self.title_row = QLabel("Журнал событий")
        self.title_row.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.title_row.setStyleSheet("""
            QLabel {
                background-color: lightblue;
                color: black;
                font-size: 14px;
                font-weight: bold;
                padding: 8px;
                border-radius: 5px 5px 0 0;
                font-family: 'Arial';
            }
        """)
        table_layout.addWidget(self.title_row)
        
        # Создаём таблицу
        self.table = QTableWidget()
        self.table.setColumnCount(4)
        self.table.setHorizontalHeaderLabels(["Время", "Тип", "Действие", "Детали"])
        
        # Настройка внешнего вида таблицы
        self.table.setAlternatingRowColors(True)
        self.table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.table.setSelectionMode(QTableWidget.SelectionMode.SingleSelection)
        self.table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        
        # Включаем отображение пустых строк
        self.table.setShowGrid(True)
        
        # Настройка ширины колонок
        header = self.table.horizontalHeader()
        header.setSectionResizeMode(0, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(1, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(2, QHeaderView.ResizeMode.ResizeToContents)
        header.setSectionResizeMode(3, QHeaderView.ResizeMode.Stretch)
        
        # Стилизация таблицы
        self.table.setStyleSheet("""
            QTableWidget {
                background-color: white;
                alternate-background-color: #f9f9f9;
                gridline-color: #ddd;
                border: 1px solid #ccc;
                border-radius: 0 0 3px 3px;
            }
            QTableWidget::item:selected {
                background-color: #3498db;
                color: white;
            }
            QHeaderView::section {
                background-color: #ecf0f1;
                padding: 5px;
                border: 1px solid #ddd;
                font-weight: bold;
            }
        """)
        
        table_layout.addWidget(self.table)
        
        # Добавляем контейнер с таблицей в основной layout
        layout.addWidget(table_container)
        
        # Статистика
        self.stats_label = QLabel("Всего записей: 0")
        self.stats_label.setAlignment(Qt.AlignmentFlag.AlignRight)
        self.stats_label.setStyleSheet("""
            QLabel {
                font-size: 12px;
                padding: 3px;
                color: #666;
            }
        """)
        layout.addWidget(self.stats_label)
        
        self.setLayout(layout)
        
        # Подключаем сигнал выбора строки
        self.table.itemSelectionChanged.connect(self.on_selection_changed)
        
        # Добавляем 5 пустых строк для наглядности
        self.add_empty_rows(5)
        
    def add_empty_rows(self, count=5):
        """Добавляет пустые строки в таблицу для наглядности"""
        for _ in range(count):
            row_position = self.table.rowCount()
            self.table.insertRow(row_position)
            
            # Заполняем пустыми значениями
            for col in range(4):
                empty_item = QTableWidgetItem("")
                empty_item.setFlags(empty_item.flags() & ~Qt.ItemFlag.ItemIsEditable)
                if col == 0:
                    empty_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
                self.table.setItem(row_position, col, empty_item)
    
    def add_row(self, action_type, action_name, details=""):
        """Добавляет новую строку в таблицу"""
        from datetime import datetime
        
        # Если есть пустые строки в конце, удаляем их перед добавлением новой
        self.remove_empty_rows()
        
        row_position = self.table.rowCount()
        self.table.insertRow(row_position)
        
        # Время
        current_time = datetime.now().strftime("%H:%M:%S")
        time_item = QTableWidgetItem(current_time)
        time_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Тип действия (с цветовой индикацией)
        type_item = QTableWidgetItem(action_type)
        type_item.setTextAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # Устанавливаем цвет для разных типов действий
        if action_type == "Файл":
            type_item.setBackground(QColor(200, 230, 255))  # светло-голубой
        elif action_type == "Эффект":
            type_item.setBackground(QColor(200, 255, 200))  # светло-зелёный
        elif action_type == "Камера":
            type_item.setBackground(QColor(255, 230, 200))  # светло-оранжевый
        elif action_type == "Система":
            type_item.setBackground(QColor(255, 200, 200))  # светло-красный
        else:
            type_item.setBackground(QColor(240, 240, 240))  # серый
        
        # Действие
        action_item = QTableWidgetItem(action_name)
        
        # Детали
        details_item = QTableWidgetItem(details)
        
        # Устанавливаем элементы в таблицу
        self.table.setItem(row_position, 0, time_item)
        self.table.setItem(row_position, 1, type_item)
        self.table.setItem(row_position, 2, action_item)
        self.table.setItem(row_position, 3, details_item)
        
        # Автоматическая прокрутка к новой строке
        self.table.scrollToBottom()
        
        # Обновляем счётчик
        self.update_stats()
        
        # Добавляем новые пустые строки для наглядности
        self.add_empty_rows(3)
        
    def remove_empty_rows(self):
        """Удаляет все пустые строки перед добавлением новой записи"""
        rows_to_remove = []
        for row in range(self.table.rowCount()):
            is_empty = True
            for col in range(4):
                item = self.table.item(row, col)
                if item and item.text().strip():
                    is_empty = False
                    break
            if is_empty:
                rows_to_remove.append(row)
        
        # Удаляем строки с конца, чтобы не нарушать индексы
        for row in reversed(rows_to_remove):
            self.table.removeRow(row)
        
    def add_file_action(self, file_path):
        """Добавляет действие с файлом"""
        import os
        filename = os.path.basename(file_path)
        self.add_row("Файл", "Открыт файл", filename)
        
    def add_effect_action(self, effect_name, params=None):
        """Добавляет действие с эффектом"""
        details = effect_name
        if params:
            param_str = ", ".join([f"{k}={v}" for k, v in params.items()])
            details += f" ({param_str})"
        self.add_row("Эффект", "Применён эффект", details)
        
    def add_camera_action(self, camera_id):
        """Добавляет действие с камерой"""
        self.add_row("Камера", "Запущена камера", f"ID: {camera_id}")
        
    def add_system_action(self, action_name, details=""):
        """Добавляет системное действие"""
        self.add_row("Система", action_name, details)
        
    def add_custom_action(self, action_type, action_name, details=""):
        """Добавляет пользовательское действие"""
        self.add_row(action_type, action_name, details)
        
    def update_stats(self):
        """Обновляет статистику таблицы"""
        # Считаем только непустые строки
        non_empty_count = 0
        for row in range(self.table.rowCount()):
            is_empty = True
            for col in range(4):
                item = self.table.item(row, col)
                if item and item.text().strip():
                    is_empty = False
                    break
            if not is_empty:
                non_empty_count += 1
        self.stats_label.setText(f"Всего записей: {non_empty_count}")
        
    def on_selection_changed(self):
        """Обработчик изменения выбора строки"""
        current_row = self.table.currentRow()
        if current_row >= 0:
            # Проверяем, не пустая ли строка
            is_empty = True
            for col in range(4):
                item = self.table.item(current_row, col)
                if item and item.text().strip():
                    is_empty = False
                    break
            
            if not is_empty:
                # Собираем данные выбранной строки
                row_data = {
                    'time': self.table.item(current_row, 0).text(),
                    'type': self.table.item(current_row, 1).text(),
                    'action': self.table.item(current_row, 2).text(),
                    'details': self.table.item(current_row, 3).text()
                }
                self.row_selected.emit(current_row, row_data)
        
    def export_to_text(self):
        """Экспорт таблицы в текстовый формат (только непустые строки)"""
        text_output = []
        text_output.append("=" * 80)
        text_output.append("Отчёт о действиях")
        text_output.append("=" * 80)
        text_output.append(f"{'Время':<10} {'Тип':<12} {'Действие':<20} {'Детали'}")
        text_output.append("-" * 80)
        
        for row in range(self.table.rowCount()):
            # Проверяем, не пустая ли строка
            is_empty = True
            time = ""
            action_type = ""
            action = ""
            details = ""
            
            for col in range(4):
                item = self.table.item(row, col)
                if item and item.text().strip():
                    is_empty = False
                    
            if not is_empty:
                time = self.table.item(row, 0).text()
                action_type = self.table.item(row, 1).text()
                action = self.table.item(row, 2).text()
                details = self.table.item(row, 3).text()
                text_output.append(f"{time:<10} {action_type:<12} {action:<20} {details}")
        
        text_output.append("-" * 80)
        text_output.append(f"Всего записей: {self.table.rowCount() - self.get_empty_rows_count()}")
        text_output.append("=" * 80)
        
        return "\n".join(text_output)
    
    def get_empty_rows_count(self):
        """Подсчитывает количество пустых строк"""
        empty_count = 0
        for row in range(self.table.rowCount()):
            is_empty = True
            for col in range(4):
                item = self.table.item(row, col)
                if item and item.text().strip():
                    is_empty = False
                    break
            if is_empty:
                empty_count += 1
        return empty_count
        
    def get_all_data(self):
        """Возвращает все данные из таблицы в виде списка словарей (только непустые строки)"""
        data = []
        for row in range(self.table.rowCount()):
            # Проверяем, не пустая ли строка
            is_empty = True
            for col in range(4):
                item = self.table.item(row, col)
                if item and item.text().strip():
                    is_empty = False
                    break
                    
            if not is_empty:
                row_data = {
                    'time': self.table.item(row, 0).text(),
                    'type': self.table.item(row, 1).text(),
                    'action': self.table.item(row, 2).text(),
                    'details': self.table.item(row, 3).text()
                }
                data.append(row_data)
        return data