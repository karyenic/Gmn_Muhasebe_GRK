from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox

class SafeSpinBox(QSpinBox):
    def wheelEvent(self, event):
        event.ignore()

class SafeDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()

def get_theme_stylesheet(font_size=11, font_weight="600"):
    return f'''
    QWidget {{
        font-family: "Segoe UI", Arial, sans-serif;
        font-size: {font_size}pt;
        color: #1a252f;
        background-color: #f4f6f7;
    }}

    QLabel {{
        font-weight: {font_weight};
        color: #2c3e50;
    }}

    QLineEdit, QComboBox, QTextEdit, QSpinBox, QDoubleSpinBox {{
        background-color: #ffffff;
        color: #2c3e50;
        border: 1px solid #bdc3c7;
        border-radius: 4px;
        padding: 6px;
        font-size: {font_size}pt;
        font-weight: 500;
    }}

    QLineEdit:focus, QComboBox:focus, QTextEdit:focus {{
        border: 2px solid #2980b9;
    }}

    QTableWidget {{
        gridline-color: #bdc3c7;
        background-color: #ffffff;
        color: #2c3e50;
        selection-background-color: #2c3e50;
        selection-color: #ffffff;
        alternate-background-color: #f8f9fa;
        font-size: {font_size}pt;
    }}

    QTableWidget::item {{
        padding: 8px 6px;
    }}

    QHeaderView::section {{
        background-color: #1a252f;
        color: #ffffff;
        font-weight: bold;
        font-size: {font_size}pt;
        padding: 8px;
        border: 1px solid #2c3e50;
    }}

    QPushButton {{
        border-radius: 5px;
        padding: 8px 18px;
        font-weight: bold;
        font-size: {font_size}pt;
        border: 1px solid rgba(0, 0, 0, 0.2);
        border-bottom: 3px solid rgba(0, 0, 0, 0.4);
    }}

    QPushButton:hover {{
        margin-top: -1px;
        border-bottom-width: 4px;
    }}

    QPushButton:pressed {{
        margin-top: 2px;
        border-bottom-width: 1px;
    }}

    QPushButton[btnClass="success"] {{ background-color: #2ecc71; color: white; border-bottom-color: #1e8449; }}
    QPushButton[btnClass="primary"] {{ background-color: #2980b9; color: white; border-bottom-color: #1f618d; }}
    QPushButton[btnClass="warning"] {{ background-color: #d35400; color: white; border-bottom-color: #a04000; }}
    QPushButton[btnClass="danger"] {{ background-color: #c0392b; color: white; border-bottom-color: #922b21; }}
    '''

LIGHT_STYLE = get_theme_stylesheet(11, "600")
MEDIUM_STYLE = get_theme_stylesheet(11, "600")
DARK_STYLE = get_theme_stylesheet(11, "600")
TACTILE_STYLE = LIGHT_STYLE
