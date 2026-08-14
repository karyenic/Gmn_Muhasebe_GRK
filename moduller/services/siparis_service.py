from moduller.database.db_manager import DBManager
class SiparisService:
    def __init__(self, db_manager: DBManager): self.db = db_manager
    def yeni_siparis_olustur(self, siparis_no, cari_id, doviz_kuru, aciklama, kalemler):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            toplam = sum(k['miktar'] * k['fiyat'] for k in kalemler)
            cursor.execute("INSERT INTO Siparisler (SiparisNo, CariID, DovizKuru, Aciklama, ToplamTutar, Durum) VALUES (?, ?, ?, ?, ?, 'Açık')", (siparis_no, cari_id, doviz_kuru, aciklama, toplam))
            siparis_id = cursor.lastrowid
            for k in kalemler:
                cursor.execute("INSERT INTO Siparis_Detay (SiparisID, UrunID, SipMiktar, SevkEdilen, Kalan, BirimFiyat, Maliyet) VALUES (?, ?, ?, 0, ?, ?, ?)", (siparis_id, k['urun_id'], k['miktar'], k['miktar'], k['fiyat'], k.get('maliyet', 0.0)))
            conn.commit()
            return siparis_id
    def siparis_guncelle(self, siparis_id, siparis_no, cari_id, doviz_kuru, aciklama, kalemler):
        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            toplam = sum(k['miktar'] * k['fiyat'] for k in kalemler)
            cursor.execute("UPDATE Siparisler SET SiparisNo=?, CariID=?, DovizKuru=?, Aciklama=?, ToplamTutar=? WHERE ID=?", (siparis_no, cari_id, doviz_kuru, aciklama, toplam, siparis_id))
            cursor.execute("DELETE FROM Siparis_Detay WHERE SiparisID=?", (siparis_id,))
            for k in kalemler:
                cursor.execute("INSERT INTO Siparis_Detay (SiparisID, UrunID, SipMiktar, SevkEdilen, Kalan, BirimFiyat, Maliyet) VALUES (?, ?, ?, 0, ?, ?, ?)", (siparis_id, k['urun_id'], k['miktar'], k['miktar'], k['fiyat'], k.get('maliyet', 0.0)))
            conn.commit()
    def siparis_sil(self, siparis_id):
        with self.db.get_connection() as conn:
            conn.execute("DELETE FROM Siparis_Detay WHERE SiparisID=?", (siparis_id,))
            conn.execute("DELETE FROM Siparisler WHERE ID=?", (siparis_id,))
            conn.commit()