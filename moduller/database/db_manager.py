import sqlite3
import os

class DBManager:
    def __init__(self, db_path=None):
        if db_path is None:
            # Proje kök dizinine göre relative yol
            base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
            db_path = os.path.join(base_dir, "Data", "firma01.db")
        
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

