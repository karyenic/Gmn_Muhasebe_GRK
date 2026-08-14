from moduller.database.db_manager import DBManager

class FaturaService:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    def fatura_olustur(self, fatura_no: str, fatura_tipi: str, cari_id: int, siparis_id: int, doviz_kuru: float, aciklama: str, kalemler: list):
        with self.db.get_connection() as conn:
            toplam_tutar = sum(item['miktar'] * item['fiyat'] for item in kalemler)
            kdv = toplam_tutar * 0.20
            genel_toplam = toplam_tutar + kdv

            # 1. Fatura Ana Kayıt
            c = conn.execute("""
                INSERT INTO Faturalar (FaturaNo, FaturaTipi, SiparisID, CariID, ToplamTutar, KDVTutari, GenelToplam, DovizKuru, Aciklama)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (fatura_no, fatura_tipi, siparis_id, cari_id, toplam_tutar, kdv, genel_toplam, doviz_kuru, aciklama))
            fatura_id = c.lastrowid

            # 2. Kalemler ve Stok Düşüşü / Girişi
            for item in kalemler:
                conn.execute("""
                    INSERT INTO Fatura_Detay (FaturaID, UrunID, Miktar, BirimFiyat, ToplamTutar)
                    VALUES (?, ?, ?, ?, ?)
                """, (fatura_id, item['urun_id'], item['miktar'], item['fiyat'], item['miktar'] * item['fiyat']))

                # Stok Yönü (Satış / Alış İade -> Stok Düşer | Alış / Satış İade -> Stok Giren)
                if fatura_tipi in ['Satış', 'Alış İade']:
                    conn.execute("UPDATE Urunler SET Miktar = Miktar - ? WHERE ID = ?", (item['miktar'], item['urun_id']))
                    conn.execute("""
                        INSERT INTO Stok_Log (UrunID, IslemTuru, EskiMiktar, YeniMiktar, Aciklama)
                        VALUES (?, ?, 0, 0, ?)
                    """, (item['urun_id'], fatura_tipi, f"Fatura No: {fatura_no} ile çıkış."))
                elif fatura_tipi in ['Alış', 'Satış İade']:
                    conn.execute("UPDATE Urunler SET Miktar = Miktar + ? WHERE ID = ?", (item['miktar'], item['urun_id']))
                    conn.execute("""
                        INSERT INTO Stok_Log (UrunID, IslemTuru, EskiMiktar, YeniMiktar, Aciklama)
                        VALUES (?, ?, 0, 0, ?)
                    """, (item['urun_id'], fatura_tipi, f"Fatura No: {fatura_no} ile giriş."))

            # 3. Cari Bakiye Entegrasyonu
            if fatura_tipi in ['Satış', 'Alış İade']:
                conn.execute("UPDATE Cari_Hesaplar SET Bakiye = Bakiye + ? WHERE ID = ?", (genel_toplam, cari_id))
            elif fatura_tipi in ['Alış', 'Satış İade']:
                conn.execute("UPDATE Cari_Hesaplar SET Bakiye = Bakiye - ? WHERE ID = ?", (genel_toplam, cari_id))

            return fatura_id

    def tum_faturalari_getir(self):
        with self.db.get_connection() as conn:
            return conn.execute("""
                SELECT f.*, c.Unvan as CariUnvan 
                FROM Faturalar f
                JOIN Cari_Hesaplar c ON f.CariID = c.ID
                ORDER BY f.ID DESC
            """).fetchall()