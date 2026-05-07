from PyQt6.QtWidgets import QWidget, QVBoxLayout, QListWidget
from PyQt6.QtCore import Qt, pyqtSignal

class DropdownMenu(QWidget):
    item_clicked = pyqtSignal(str)  # Добавляем сигнал
    
    def __init__(self, items, parent=None):
        super().__init__(parent)
        self.setWindowFlags(Qt.WindowType.Popup)
        
        layout = QVBoxLayout()
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        self.list_widget = QListWidget()
        self.list_widget.addItems(items)
        self.list_widget.itemClicked.connect(lambda item: self.item_clicked.emit(item.text()))
        self.list_widget.setSizeAdjustPolicy(QListWidget.SizeAdjustPolicy.AdjustToContents)
        self.list_widget.setMaximumHeight(200)
        self.list_widget.setFocusPolicy(Qt.FocusPolicy.NoFocus)
        self.list_widget.setStyleSheet("""
            QListWidget {
                background-color: lavender;
                border: 1px solid #ccc;
                font-size: 14px;
            }
            QListWidget::item {
                padding: 8px 20px;
            }
            QListWidget::item:hover {
                background-color: lightblue;
            }
            QListWidget::item:selected {
                background-color: lightskyblue;
            }
        """)
        
        layout.addWidget(self.list_widget)
        self.setLayout(layout)
    
    def show_at_position(self, x, y):
        self.move(x, y)
        self.list_widget.clearSelection()
        self.show()
        self.raise_()