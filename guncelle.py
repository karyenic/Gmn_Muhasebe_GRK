import os

db_manager_path = r"C:\Gmn_Muhasebe\moduller\database\db_manager.py"
styles_path = r"C:\Gmn_Muhasebe\moduller\ui\styles.py"

db_code = """import sqlite3
import os

class DBManager:
    def __init__(self, db_path=r"C:\\Gmn_Muhasebe\\data\\firma01.db"):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def set_active_db(self, db_path):
        self.db_path = db_path
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.init_db()

    def get_connection(self):
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def init_db(self):
        with self.get_connection() as conn:
            cur = conn.cursor()
            schema_file = os.path.join(os.path.dirname(__file__), 'schema.sql')
            if os.path.exists(schema_file):
                with open(schema_file, 'r', encoding='utf-8') as f:
                    cur.executescript(f.read())
            
            cur.execute("CREATE TABLE IF NOT EXISTS Kasa_Hareketleri (ID INTEGER PRIMARY KEY AUTOINCREMENT, CariID INTEGER, IslemTuru TEXT, Tutar REAL DEFAULT 0, Aciklama TEXT, Tarih DATETIME DEFAULT CURRENT_TIMESTAMP)")
            cur.execute("CREATE TABLE IF NOT EXISTS Irsaliye_Detay (ID INTEGER PRIMARY KEY AUTOINCREMENT, SevkiyatID INTEGER, UrunID INTEGER, Miktar REAL DEFAULT 0, BirimFiyat REAL DEFAULT 0)")
            cur.execute("CREATE TABLE IF NOT EXISTS Siparis_Detay (ID INTEGER PRIMARY KEY AUTOINCREMENT, SiparisID INTEGER, UrunID INTEGER, Miktar REAL DEFAULT 0, SevkEdilen REAL DEFAULT 0, BirimFiyat REAL DEFAULT 0)")
            
            self.check_and_add_columns(cur, 'Siparis_Detay', 'UrunID', 'INTEGER DEFAULT 0')
            self.check_and_add_columns(cur, 'Siparis_Detay', 'Miktar', 'REAL DEFAULT 0')
            self.check_and_add_columns(cur, 'Siparis_Detay', 'SevkEdilen', 'REAL DEFAULT 0')
            self.check_and_add_columns(cur, 'Siparis_Detay', 'BirimFiyat', 'REAL DEFAULT 0')
            
            self.check_and_add_columns(cur, 'Siparisler', 'SiparisTipi', "TEXT DEFAULT 'Musteri Siparisi (Satis)'")
            self.check_and_add_columns(cur, 'Cari_Hesaplar', 'VadeGunu', 'INTEGER DEFAULT 30')
            self.check_and_add_columns(cur, 'Faturalar', 'VadeTarihi', 'DATETIME')
            self.check_and_add_columns(cur, 'Faturalar', 'IrsaliyeNo', "TEXT DEFAULT ''")
            self.check_and_add_columns(cur, 'Faturalar', 'AraToplam', 'REAL DEFAULT 0')
            self.check_and_add_columns(cur, 'Faturalar', 'IskontoTutar', 'REAL DEFAULT 0')
            self.check_and_add_columns(cur, 'Faturalar', 'Masraf', 'REAL DEFAULT 0')
            self.check_and_add_columns(cur, 'Faturalar', 'KDVTutari', 'REAL DEFAULT 0')
            self.check_and_add_columns(cur, 'Faturalar', 'GenelToplam', 'REAL DEFAULT 0')
            self.check_and_add_columns(cur, 'Urunler', 'IsPaket', 'INTEGER DEFAULT 0')
            self.check_and_add_columns(cur, 'Urunler', 'Maliyet', 'REAL DEFAULT 0')
            
            conn.commit()

    def check_and_add_columns(self, cursor, table, column, col_type):
        cursor.execute(f"PRAGMA table_info({table})")
        columns = [row['name'] for row in cursor.fetchall()]
        if column not in columns:
            cursor.execute(f"ALTER TABLE {table} ADD COLUMN {column} {col_type}")
"""

styles_code = """from PyQt5.QtWidgets import QSpinBox, QDoubleSpinBox

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
"""

os.makedirs(os.path.dirname(db_manager_path), exist_ok=True)
os.makedirs(os.path.dirname(styles_path), exist_ok=True)

with open(db_manager_path, "w", encoding="utf-8") as f:
    f.write(db_code)

with open(styles_path, "w", encoding="utf-8") as f:
    f.write(styles_code)

print("BAŞARILI: Modüller sorunsuz güncellendi.")