# C:\Gmn_Muhasebe\moduller\services\cari_service.py

from moduller.database.db_manager import DBManager

class CariService:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    def get_cariler(self):
        """Tüm Cari Hesapları getirir"""
        query = "SELECT * FROM Cari_Hesaplar WHERE Durum != 'Pasif' ORDER BY Unvan ASC"
        with self.db.get_connection() as conn:
            return conn.execute(query).fetchall()

    def get_tum_cariler(self):
        """AttributeError önlemek için get_cariler ile aynı işlevi gören alias"""
        return self.get_cariler()

    def get_cari_by_id(self, cari_id: int):
        query = "SELECT * FROM Cari_Hesaplar WHERE ID = ?"
        with self.db.get_connection() as conn:
            return conn.execute(query, (cari_id,)).fetchone()

    def cari_ekle_veya_guncelle(self, c_data: dict):
        with self.db.get_connection() as conn:
            cur = conn.cursor()
            if c_data.get('id'):
                cur.execute("""
                    UPDATE Cari_Hesaplar SET
                        CariKodu=?, Unvan=?, YetkiliKisi=?, Telefon=?, Eposta=?,
                        VergiDairesi=?, VergiNo=?, Adres=?
                    WHERE ID=?
                """, (
                    c_data['cari_kodu'], c_data['unvan'], c_data.get('yetkili_kisi', ''),
                    c_data.get('telefon', ''), c_data.get('eposta', ''),
                    c_data.get('vergi_dairesi', ''), c_data.get('vergi_no', ''),
                    c_data.get('adres', ''), c_data['id']
                ))
            else:
                cur.execute("""
                    INSERT INTO Cari_Hesaplar (CariKodu, Unvan, YetkiliKisi, Telefon, Eposta, VergiDairesi, VergiNo, Adres, Bakiye, Durum)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 0.0, 'Aktif')
                """, (
                    c_data['cari_kodu'], c_data['unvan'], c_data.get('yetkili_kisi', ''),
                    c_data.get('telefon', ''), c_data.get('eposta', ''),
                    c_data.get('vergi_dairesi', ''), c_data.get('vergi_no', ''),
                    c_data.get('adres', '')
                ))
            conn.commit()

    def get_cari_ekstre(self, cari_id: int):
        """Cari Kart Yürüyen Bakiye & Ekstre Sorgusu (Faturalar ve Kasa Hareketleri)"""
        query = """
            SELECT FaturaTipi as EvrakTuru, FaturaNo as EvrakNo, Tarih,
                   CASE WHEN FaturaTipi = 'Satış Faturası' THEN GenelToplam ELSE 0 END as Borc,
                   CASE WHEN FaturaTipi = 'Alış Faturası' THEN GenelToplam ELSE 0 END as Alacak
            FROM Faturalar
            WHERE CariID = ?
            
            UNION ALL
            
            SELECT IslemTuru as EvrakTuru, ('KASA-' || ID) as EvrakNo, Tarih,
                   CASE WHEN IslemTuru IN ('Tediye', 'Çıkış', 'Ödeme') THEN Tutar ELSE 0 END as Borc,
                   CASE WHEN IslemTuru IN ('Tahsilat', 'Giriş') THEN Tutar ELSE 0 END as Alacak
            FROM Kasa_Hareketleri
            WHERE CariID = ?
            
            ORDER BY Tarih ASC
        """
        with self.db.get_connection() as conn:
            return conn.execute(query, (cari_id, cari_id)).fetchall()