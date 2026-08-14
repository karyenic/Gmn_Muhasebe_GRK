# C:\Gmn_Muhasebe\moduller\services\stok_service.py

import datetime
import uuid
from moduller.database.db_manager import DBManager

class StokService:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    def stok_kodu_var_mi(self, urun_kodu: str, haric_id: int = None) -> bool:
        with self.db.get_connection() as conn:
            if haric_id:
                res = conn.execute("SELECT COUNT(*) as cnt FROM Urunler WHERE UrunKodu = ? COLLATE NOCASE AND ID != ?", (urun_kodu.strip(), haric_id)).fetchone()
            else:
                res = conn.execute("SELECT COUNT(*) as cnt FROM Urunler WHERE UrunKodu = ? COLLATE NOCASE", (urun_kodu.strip(),)).fetchone()
            return res['cnt'] > 0

    def urun_ekle_veya_guncelle(self, urun_data: dict, recete_list: list = None) -> int:
        if self.stok_kodu_var_mi(urun_data['urun_kodu'], urun_data.get('id')):
            raise ValueError(f"'{urun_data['urun_kodu']}' stok kodu zaten kullanılıyor!")

        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.db.get_connection() as conn:
            cursor = conn.cursor()
            
            eski_miktar = 0.0
            if urun_data.get('id'):
                eski_urun = cursor.execute("SELECT Miktar FROM Urunler WHERE ID=?", (urun_data['id'],)).fetchone()
                if eski_urun and eski_urun['Miktar'] is not None: 
                    eski_miktar = float(eski_urun['Miktar'])

            yeni_miktar = float(urun_data.get('miktar', 0.0))
            eklenen_paket_miktari = yeni_miktar - eski_miktar

            maliyet = float(urun_data.get('maliyet', 0.0))
            if urun_data.get('is_paket', 0) == 1 and recete_list:
                hesaplanan_maliyet = 0.0
                for item in recete_list:
                    alt_u = cursor.execute("SELECT Maliyet FROM Urunler WHERE ID=?", (item['alt_urun_id'],)).fetchone()
                    alt_maliyet = float(alt_u['Maliyet']) if alt_u and alt_u['Maliyet'] else 0.0
                    hesaplanan_maliyet += alt_maliyet * float(item['miktar'])
                maliyet = hesaplanan_maliyet

            if urun_data.get('id'):
                cursor.execute("""
                    UPDATE Urunler SET
                        UrunKodu=?, UrunAdi=?, Birim=?, Maliyet=?, SatisFiyati=?,
                        KdvOrani=?, Miktar=?, IsPaket=?
                    WHERE ID=?
                """, (
                    urun_data['urun_kodu'].strip(), urun_data['urun_adi'].strip(), urun_data.get('birim', 'Adet'),
                    maliyet, urun_data.get('satis_fiyati', 0.0),
                    urun_data.get('kdv_orani', 20), yeni_miktar,
                    urun_data.get('is_paket', 0), urun_data['id']
                ))
                urun_id = urun_data['id']
            else:
                cursor.execute("""
                    INSERT INTO Urunler (UrunKodu, UrunAdi, Birim, Maliyet, SatisFiyati, KdvOrani, Miktar, IsPaket)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    urun_data['urun_kodu'].strip(), urun_data['urun_adi'].strip(), urun_data.get('birim', 'Adet'),
                    maliyet, urun_data.get('satis_fiyati', 0.0),
                    urun_data.get('kdv_orani', 20), yeni_miktar, urun_data.get('is_paket', 0)
                ))
                urun_id = cursor.lastrowid

            if urun_data.get('is_paket', 0) == 1 and recete_list is not None:
                cursor.execute("DELETE FROM Paket_Recete WHERE AnaUrunID=?", (urun_id,))
                for item in recete_list:
                    alt_id = int(item['alt_urun_id'])
                    alt_mikt = float(item['miktar'])
                    cursor.execute("INSERT INTO Paket_Recete (AnaUrunID, AltUrunID, Miktar) VALUES (?, ?, ?)", (urun_id, alt_id, alt_mikt))

                    if eklenen_paket_miktari > 0:
                        alt_dusulecek = eklenen_paket_miktari * alt_mikt
                        cursor.execute("UPDATE Urunler SET Miktar = Miktar - ? WHERE ID = ?", (alt_dusulecek, alt_id))

                        unique_id = str(uuid.uuid4())[:8].upper()
                        cur_evrak_no = f"MNT-{urun_data['urun_kodu']}-{unique_id}"
                        
                        cursor.execute("""
                            INSERT INTO Sevkiyatlar (SiparisID, EvrakTuru, SevkiyatNo, Tarih, CariID)
                            VALUES (0, 'İmalat Montaj Çıkışı', ?, ?, 0)
                        """, (cur_evrak_no, now_str))
                        sevk_id = cursor.lastrowid
                        
                        cursor.execute("""
                            INSERT INTO Irsaliye_Detay (SevkiyatID, UrunID, Miktar, BirimFiyat)
                            VALUES (?, ?, ?, 0)
                        """, (sevk_id, alt_id, alt_dusulecek))

            conn.commit()
            return urun_id

    def get_stok_hareket_foyler(self, urun_id: int):
        query = """
            SELECT 'Fatura' as EvrakTuru, f.FaturaNo as EvrakNo, f.Tarih, f.FaturaTipi as Aciklama,
                   fd.Miktar, fd.BirimFiyat, f.ID as FaturaID
            FROM Fatura_Detay fd
            JOIN Faturalar f ON fd.FaturaID = f.ID
            WHERE fd.UrunID = ?
            
            UNION ALL
            
            SELECT 'İrsaliye / Sevkiyat' as EvrakTuru, s.SevkiyatNo as EvrakNo, s.Tarih, s.EvrakTuru as Aciklama,
                   idt.Miktar, idt.BirimFiyat, s.ID as FaturaID
            FROM Irsaliye_Detay idt
            JOIN Sevkiyatlar s ON idt.SevkiyatID = s.ID
            WHERE idt.UrunID = ?

            UNION ALL

            SELECT 'Sipariş Sevk İrsaliyesi' as EvrakTuru, s.SevkiyatNo as EvrakNo, s.Tarih, 'Siparişten Kısmi Sevk' as Aciklama,
                   sd.SevkEdilen as Miktar, sd.BirimFiyat, s.ID as FaturaID
            FROM Sevkiyatlar s
            JOIN Siparis_Detay sd ON sd.SiparisID = s.SiparisID
            WHERE sd.UrunID = ? AND s.SiparisID > 0 AND sd.SevkEdilen > 0
            
            ORDER BY Tarih DESC
        """
        with self.db.get_connection() as conn:
            return conn.execute(query, (urun_id, urun_id, urun_id)).fetchall()

    def get_recete_elemanlari(self, ana_urun_id: int):
        query = "SELECT pr.*, u.UrunKodu, u.UrunAdi, u.Maliyet FROM Paket_Recete pr JOIN Urunler u ON pr.AltUrunID = u.ID WHERE pr.AnaUrunID = ?"
        with self.db.get_connection() as conn:
            return conn.execute(query, (ana_urun_id,)).fetchall()

    def get_tum_alt_urunler(self, haric_ana_urun_id: int = None):
        with self.db.get_connection() as conn:
            if haric_ana_urun_id:
                return conn.execute("SELECT ID, UrunKodu, UrunAdi, Maliyet FROM Urunler WHERE ID != ? ORDER BY UrunKodu ASC", (haric_ana_urun_id,)).fetchall()
            return conn.execute("SELECT ID, UrunKodu, UrunAdi, Maliyet FROM Urunler ORDER BY UrunKodu ASC").fetchall()