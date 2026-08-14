# C:\Gmn_Muhasebe\moduller\services\sevkiyat_service.py

import datetime
from moduller.database.db_manager import DBManager

class SevkiyatService:
    def __init__(self, db_manager: DBManager):
        self.db = db_manager

    def siparis_sevk_et(self, siparis_id: int, evrak_turu: str, evrak_no: str, sevk_kalemleri: list):
        """
        Siparişi sevk eder.
        - Stok Yetersizlik Koruması: Depodaki fiziki miktar sevk miktarından azsa işlem durdurulur (Rollback).
        - Satış Anında Sadece Sevk Edilen Ana/Paket Ürün Düşülür (Alt parçalar montaj anında düştüğü için mükerrer düşüm yapılmaz).
        """
        with self.db.get_connection() as conn:
            cur = conn.cursor()

            # 1. Sipariş Var mı Kontrolü
            sip = cur.execute("SELECT * FROM Siparisler WHERE ID = ?", (siparis_id,)).fetchone()
            if not sip:
                raise ValueError("Sevk edilmek istenen sipariş bulunamadı!")

            cari_id = sip['CariID']
            toplam_sevk_tutari = 0.0
            toplam_kdv_tutari = 0.0
            suan_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # 2. STOK YETERLİLİK VE MİKTAR KONTROLÜ (Negatif Stok Koruması)
            for kalem in sevk_kalemleri:
                u_id = kalem['urun_id']
                mikt = kalem['sevk_miktar']

                urun = cur.execute("SELECT UrunKodu, UrunAdi, Miktar FROM Urunler WHERE ID = ?", (u_id,)).fetchone()
                if not urun:
                    raise ValueError(f"ID: {u_id} olan ürün veritabanında bulunamadı!")

                mevcut_stok = float(urun['Miktar'])
                if mevcut_stok < mikt:
                    raise ValueError(
                        f"❌ YETERSİZ STOK!\n\n"
                        f"Ürün: {urun['UrunKodu']} - {urun['UrunAdi']}\n"
                        f"Depodaki Stok: {int(mevcut_stok)} Adet\n"
                        f"Sevk Edilmek İstenen: {int(mikt)} Adet\n\n"
                        f"Lütfen önce stok girişi yapın veya sevk miktarını düşürün."
                    )

            # 3. Sevkiyat Üst Kaydı Oluşturma
            cur.execute("""
                INSERT INTO Sevkiyatlar (SiparisID, EvrakTuru, SevkiyatNo, Tarih, CariID)
                VALUES (?, ?, ?, ?, ?)
            """, (siparis_id, evrak_turu, evrak_no, suan_str, cari_id))

            hazirlanan_kalemler = []

            # 4. Kalem Bazlı Stok Düşüşü
            for kalem in sevk_kalemleri:
                sd_id = kalem['siparis_detay_id']
                u_id = kalem['urun_id']
                mikt = kalem['sevk_miktar']
                fiy = kalem['birim_fiyat']

                satir_tutari = mikt * fiy
                toplam_sevk_tutari += satir_tutari

                urun = cur.execute("SELECT KdvOrani FROM Urunler WHERE ID = ?", (u_id,)).fetchone()
                kdv_orani = float(dict(urun).get('KdvOrani', 20.0)) if urun else 20.0
                satir_kdv = satir_tutari * (kdv_orani / 100.0)
                toplam_kdv_tutari += satir_kdv

                hazirlanan_kalemler.append({
                    'urun_id': u_id,
                    'miktar': mikt,
                    'birim_fiyat': fiy,
                    'kdv_orani': kdv_orani
                })

                # Sipariş Kalan Miktarını Güncelle
                cur.execute("""
                    UPDATE Siparis_Detay 
                    SET SevkEdilen = SevkEdilen + ?, Kalan = Kalan - ? 
                    WHERE ID = ?
                """, (mikt, mikt, sd_id))

                # Depodaki Fiziki Stoğu Düş (Sadece Satılan/Sevk Edilen Ürün)
                cur.execute("UPDATE Urunler SET Miktar = Miktar - ? WHERE ID = ?", (mikt, u_id))

            # 5. Evrak Türü Fatura İse Fatura ve Cari Hesap Kaydı
            if evrak_turu == "Fatura":
                genel_toplam = toplam_sevk_tutari + toplam_kdv_tutari

                cur.execute("""
                    INSERT INTO Faturalar (FaturaNo, FaturaTipi, CariID, ToplamTutar, AraToplam, IskontoTutar, Masraf, KDVTutari, GenelToplam, Tarih)
                    VALUES (?, 'Satış Faturası', ?, ?, ?, 0, 0, ?, ?, ?)
                """, (evrak_no, cari_id, toplam_sevk_tutari, toplam_sevk_tutari, toplam_kdv_tutari, genel_toplam, suan_str))
                fatura_id = cur.lastrowid

                for hk in hazirlanan_kalemler:
                    cur.execute("""
                        INSERT INTO Fatura_Detay (FaturaID, UrunID, Miktar, BirimFiyat, IskontoOran, KdvOrani)
                        VALUES (?, ?, ?, ?, 0, ?)
                    """, (fatura_id, hk['urun_id'], hk['miktar'], hk['birim_fiyat'], hk['kdv_orani']))

                # Cari Hesaba Borç İşle
                cur.execute("UPDATE Cari_Hesaplar SET Bakiye = Bakiye + ? WHERE ID = ?", (genel_toplam, cari_id))

            # 6. Sipariş Kapanma / Kısmi Sevk Durum Güncellemesi
            kalan_toplam = cur.execute("SELECT SUM(Kalan) as k FROM Siparis_Detay WHERE SiparisID = ?", (siparis_id,)).fetchone()['k'] or 0
            if kalan_toplam <= 0:
                cur.execute("UPDATE Siparisler SET Durum = 'Kapalı' WHERE ID = ?", (siparis_id,))
            else:
                cur.execute("UPDATE Siparisler SET Durum = 'Kısmi Sevk' WHERE ID = ?", (siparis_id,))

            conn.commit()