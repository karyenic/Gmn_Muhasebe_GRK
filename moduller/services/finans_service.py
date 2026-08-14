# C:\Gmn_Muhasebe\moduller\services\finans_service.py

import datetime
from moduller.database.db_manager import DBManager

class FinansService:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    def kasa_islemi_ekle(self, cari_id: int, islem_turu: str, tutar: float, aciklama: str = ""):
        """
        Kasa Tahsilat / Tediye İşlemi
        - IslemTuru: 'Tahsilat' veya 'Tediye'
        - Tahsilat: Kasaya Para Girer (+), Cari Bakiye Düşer (-)
        - Tediye: Kasadan Para Çıkar (-), Cari Bakiye Artar / Alacak Kapanır (+)
        """
        suan_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        tutar = float(tutar)

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            
            # 1. Kasa Hareket Kaydı
            cur.execute("""
                INSERT INTO Kasa_Hareketleri (CariID, IslemTuru, Tutar, Aciklama, Tarih)
                VALUES (?, ?, ?, ?, ?)
            """, (cari_id, islem_turu, tutar, aciklama, suan_str))

            # 2. Cari Bakiye Güncellemesi
            if islem_turu in ['Tahsilat', 'Giriş', 'Tahsilat Fişi']:
                cur.execute("UPDATE Cari_Hesaplar SET Bakiye = Bakiye - ? WHERE ID = ?", (tutar, cari_id))
            elif islem_turu in ['Tediye', 'Çıkış', 'Tediye Fişi', 'Ödeme']:
                cur.execute("UPDATE Cari_Hesaplar SET Bakiye = Bakiye + ? WHERE ID = ?", (tutar, cari_id))

            conn.commit()

    def get_kasa_hareketleri(self):
        query = """
            SELECT kh.*, c.Unvan, c.CariKodu
            FROM Kasa_Hareketleri kh
            LEFT JOIN Cari_Hesaplar c ON kh.CariID = c.ID
            ORDER BY kh.Tarih DESC
        """
        with self.db.get_connection() as conn:
            return conn.execute(query).fetchall()