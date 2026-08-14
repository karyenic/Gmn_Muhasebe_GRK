# C:\Gmn_Muhasebe\moduller\ui\siparis_ui.py

import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QHeaderView, QDialog, QMessageBox, QLabel,
    QLineEdit, QComboBox, QAbstractItemView, QTextEdit, QRadioButton, QButtonGroup, QTabWidget
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from moduller.ui.styles import SafeSpinBox, SafeDoubleSpinBox

def row_get(row, key, default=None):
    if not row: return default
    try:
        for k in row.keys():
            if k.lower() == key.lower():
                val = row[k]
                return val if val is not None else default
    except Exception: pass
    return default

def format_tarih_tr_saat(tarih_str):
    if not tarih_str: return ""
    try:
        tarih_str = str(tarih_str)
        if " " in tarih_str:
            t_parca, s_parca = tarih_str.split(" ")
            y, m, d = t_parca.split("-")
            s_parca = ":".join(s_parca.split(":")[:2])
            return f"{d}/{m}/{y} {s_parca}"
        elif "-" in tarih_str:
            y, m, d = tarih_str.split("-")
            return f"{d}/{m}/{y}"
        return str(tarih_str)
    except Exception: return str(tarih_str)

class SevkiyatOnayDialog(QDialog):
    def __init__(self, parent):
        super().__init__(parent)
        self.setWindowTitle("🚚 Sevkiyat Belgesi Türü Seçimi")
        self.resize(500, 240)
        
        l = QVBoxLayout(self)
        l.addWidget(QLabel("<b>Bu Sevkiyat İçin Hangi Belge Oluşturulsun?</b>"))

        self.btn_grp = QButtonGroup(self)
        self.rb_irsaliye = QRadioButton("📄 Sadece İrsaliye Kesilsin (Stok Düşer, Fatura Sonra Kesilecek)")
        self.rb_fatura = QRadioButton("🧾 Doğrudan Fatura Kesilsin (Stok Düşer, Cari Bakiyeye Borç İşlenir)")
        self.rb_irsaliye.setChecked(True)

        self.btn_grp.addButton(self.rb_irsaliye)
        self.btn_grp.addButton(self.rb_fatura)

        l.addWidget(self.rb_irsaliye)
        l.addWidget(self.rb_fatura)

        btn_onay = QPushButton("🚀 Sevkiyatı Başlat ve Belgeyi Düzenle")
        btn_onay.setProperty("btnClass", "success")
        btn_onay.clicked.connect(self.accept)
        l.addWidget(btn_onay)

    def is_fatura(self):
        return self.rb_fatura.isChecked()

class SiparisDialog(QDialog):
    def __init__(self, parent, db, siparis_id=None):
        super().__init__(parent)
        self.db = db
        self.siparis_id = siparis_id
        self.is_completed = False
        self.setWindowTitle("🛒 Sipariş Detayı & Kısmi / Tam Sevkiyat Yönetimi" if siparis_id else "➕ Yeni Müşteri / Tedarikçi Siparişi")
        self.resize(1350, 850) # GENİŞ FERAH BÜYÜK PENCERE
        self.setup_ui()
        self.load_cariler()
        self.load_urunler()
        if self.siparis_id:
            self.load_siparis_data()
            self.load_sevkiyat_gecmisi()

    def setup_ui(self):
        l = QVBoxLayout(self)

        top = QHBoxLayout()
        self.cmb_tip = QComboBox()
        self.cmb_tip.addItems(["Müşteri Siparişi (Satış)", "Tedarikçi Siparişi (Alış)"])

        self.cmb_cari = QComboBox()
        now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        self.txt_no = QLineEdit(f"SIP-{now_str}")

        top.addWidget(QLabel("<b>Sipariş Türü:</b>")); top.addWidget(self.cmb_tip)
        top.addWidget(QLabel("<b>Cari / Firma:</b>")); top.addWidget(self.cmb_cari, 2)
        top.addWidget(QLabel("<b>Sipariş No:</b>")); top.addWidget(self.txt_no)
        l.addLayout(top)

        self.tabs_main = QTabWidget()

        # TAB 1: Sipariş Kalemleri
        w_kalemler = QWidget()
        l_k = QVBoxLayout(w_kalemler)

        self.btn_satir = QPushButton("+ Sipariş Kalemi / Ürün Ekle")
        self.btn_satir.setProperty("btnClass", "success")
        self.btn_satir.clicked.connect(self.add_satir)
        l_k.addWidget(self.btn_satir, alignment=Qt.AlignLeft)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["Ürün Kodu / Adı", "Top. Sipariş", "Önceki Sevk", "Bu Sevk Miktarı", "Birim Fiyat (₺)", "Satır Toplamı (₺)", "İşlem"])
        
        header = self.table.horizontalHeader()
        for c in range(7): header.setSectionResizeMode(c, QHeaderView.Interactive)
        header.setSectionResizeMode(0, QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(40) # FERAH SATIR YÜKSEKLİĞİ
        
        l_k.addWidget(self.table)

        self.lbl_toplam = QLabel("<b>Sipariş Toplam Tutarı: ₺ 0.00</b>")
        self.lbl_toplam.setStyleSheet("font-size: 13pt; color: #2c3e50; font-weight: bold;")
        l_k.addWidget(self.lbl_toplam, alignment=Qt.AlignRight)

        l_k.addWidget(QLabel("<b>Sipariş Notları / Açıklama:</b>"))
        self.txt_notlar = QTextEdit()
        self.txt_notlar.setMaximumHeight(45)
        l_k.addWidget(self.txt_notlar)

        self.tabs_main.addTab(w_kalemler, "📋 Sipariş İçeriği & Sevk Miktarları")

        # TAB 2: Sevkiyat Geçmişi Tablosu
        if self.siparis_id:
            w_gecmis = QWidget()
            l_g = QVBoxLayout(w_gecmis)

            self.tbl_gecmis = QTableWidget()
            self.tbl_gecmis.setColumnCount(5)
            self.tbl_gecmis.setHorizontalHeaderLabels(["Evrak Türü", "Evrak / İrsaliye No", "Tarih & Saat", "Sevk Edilen Ürün", "Miktar"])
            
            g_header = self.tbl_gecmis.horizontalHeader()
            for c in range(5): g_header.setSectionResizeMode(c, QHeaderView.Interactive)
            g_header.setSectionResizeMode(3, QHeaderView.Stretch)
            self.tbl_gecmis.verticalHeader().setDefaultSectionSize(38)
            self.tbl_gecmis.setEditTriggers(QAbstractItemView.NoEditTriggers)

            l_g.addWidget(self.tbl_gecmis)
            self.tabs_main.addTab(w_gecmis, "🚚 Geçmiş Sevkiyatlar / İrsaliye Kayıtları")

        l.addWidget(self.tabs_main)

        self.btn_save = QPushButton("💾 Sipariş Bilgilerini Kaydet")
        self.btn_save.setProperty("btnClass", "primary")
        self.btn_save.clicked.connect(self.save)
        l.addWidget(self.btn_save)

        if self.siparis_id:
            self.btn_sevk = QPushButton("🚚 GİRİLEN MİKTAR KADAR SEVK ET (İRSALİYE / FATURA KES)")
            self.btn_sevk.setProperty("btnClass", "warning")
            self.btn_sevk.setStyleSheet("font-size: 12pt; padding: 12px; font-weight: bold;")
            self.btn_sevk.clicked.connect(self.sevk_et)
            l.addWidget(self.btn_sevk)

    def load_cariler(self):
        self.cariler_map = {}
        with self.db.get_connection() as conn:
            for c in conn.execute("SELECT ID, CariKodu, Unvan FROM Cari_Hesaplar WHERE Durum != 'Pasif' ORDER BY Unvan ASC").fetchall():
                lbl = f"{c['CariKodu']} - {c['Unvan']}"
                self.cariler_map[lbl] = c['ID']
                self.cmb_cari.addItem(lbl)

    def load_urunler(self):
        with self.db.get_connection() as conn:
            self.urunler = conn.execute("SELECT ID, UrunKodu, UrunAdi, SatisFiyati, KdvOrani FROM Urunler").fetchall()

    def add_satir(self, urun_id=None, miktar=1, sevk=0, fiyat=0.0, detay_id=None):
        r = self.table.rowCount()
        self.table.insertRow(r)

        cmb_u = QComboBox()
        for u in self.urunler:
            cmb_u.addItem(f"{u['UrunKodu']} - {u['UrunAdi']}", dict(u))
            if urun_id and u['ID'] == urun_id:
                cmb_u.setCurrentIndex(cmb_u.count() - 1)

        spn_m = SafeSpinBox(); spn_m.setRange(1, 99999); spn_m.setValue(int(miktar)); spn_m.valueChanged.connect(self.hesapla_toplam)
        lbl_sevk = QLabel(f" {int(sevk)} Adet ")
        lbl_sevk.setAlignment(Qt.AlignCenter)
        
        kalan = max(0, int(miktar) - int(sevk))
        spn_bu_sevk = SafeSpinBox()
        spn_bu_sevk.setRange(0, kalan if kalan > 0 else 99999)
        spn_bu_sevk.setValue(kalan)
        spn_bu_sevk.setStyleSheet("background-color: #e8f8f5; font-weight: bold; color: #16a085;")

        spn_f = SafeDoubleSpinBox(); spn_f.setRange(0, 999999); spn_f.setValue(float(fiyat)); spn_f.valueChanged.connect(self.hesapla_toplam)

        btn_del = QPushButton("❌")
        btn_del.setProperty("btnClass", "danger")
        btn_del.clicked.connect(lambda: (self.table.removeRow(self.table.currentRow()), self.hesapla_toplam()))

        # TAMAMLANMIŞ SİPARİŞ KİLİTLEME
        if self.is_completed:
            spn_m.setReadOnly(True)
            spn_bu_sevk.setReadOnly(True)
            spn_f.setReadOnly(True)
            cmb_u.setEnabled(False)
            btn_del.setEnabled(False)

        self.table.setCellWidget(r, 0, cmb_u)
        self.table.setCellWidget(r, 1, spn_m)
        self.table.setCellWidget(r, 2, lbl_sevk)
        self.table.setCellWidget(r, 3, spn_bu_sevk)
        self.table.setCellWidget(r, 4, spn_f)
        self.table.setItem(r, 5, QTableWidgetItem("₺ 0.00"))
        self.table.setCellWidget(r, 6, btn_del)

        if detay_id: cmb_u.setProperty("detay_id", detay_id)
        cmb_u.currentIndexChanged.connect(lambda: self.satir_urun_secildi(r, cmb_u))
        if not urun_id and self.urunler: self.satir_urun_secildi(r, cmb_u)
        self.hesapla_toplam()

    def satir_urun_secildi(self, row, cmb):
        u = cmb.currentData()
        if u: self.table.cellWidget(row, 4).setValue(float(u.get('SatisFiyati', 0.0)))
        self.hesapla_toplam()

    def hesapla_toplam(self):
        tot = 0.0
        for r in range(self.table.rowCount()):
            spn_m = self.table.cellWidget(r, 1)
            spn_f = self.table.cellWidget(r, 4)
            if spn_m and spn_f:
                st = spn_m.value() * spn_f.value()
                tot += st
                it_tot = QTableWidgetItem(f"₺ {st:,.2f}")
                it_tot.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(r, 5, it_tot)
        self.lbl_toplam.setText(f"<b>Sipariş Toplam Tutarı: ₺ {tot:,.2f}</b>")
        return tot

    def load_siparis_data(self):
        with self.db.get_connection() as conn:
            sp = conn.execute("SELECT * FROM Siparisler WHERE ID = ?", (self.siparis_id,)).fetchone()
            if sp:
                durum = row_get(sp, 'Durum', '')
                if durum == 'Tamamlandı':
                    self.is_completed = True
                    self.btn_save.setEnabled(False)
                    if hasattr(self, 'btn_sevk'): self.btn_sevk.setEnabled(False)
                    self.btn_satir.setEnabled(False)

                self.txt_no.setText(row_get(sp, 'SiparisNo', ''))
                self.txt_notlar.setText(row_get(sp, 'Aciklama', ''))
                c = conn.execute("SELECT CariKodu, Unvan FROM Cari_Hesaplar WHERE ID = ?", (row_get(sp, 'CariID', 0),)).fetchone()
                if c:
                    lbl = f"{row_get(c, 'CariKodu', '')} - {row_get(c, 'Unvan', '')}"
                    idx = self.cmb_cari.findText(lbl)
                    if idx >= 0: self.cmb_cari.setCurrentIndex(idx)

                detaylar = conn.execute("SELECT * FROM Siparis_Detay WHERE SiparisID = ?", (self.siparis_id,)).fetchall()
                self.table.setRowCount(0)
                for d in detaylar:
                    u_id = row_get(d, 'UrunID', None)
                    mikt = row_get(d, 'Miktar', 1.0)
                    sevk_mikt = row_get(d, 'SevkEdilen', 0.0)
                    fiyat = row_get(d, 'BirimFiyat', 0.0)
                    d_id = row_get(d, 'ID', None)
                    self.add_satir(u_id, mikt, sevk_mikt, fiyat, d_id)

    def load_sevkiyat_gecmisi(self):
        if not hasattr(self, 'tbl_gecmis'): return
        with self.db.get_connection() as conn:
            sevkler = conn.execute("""
                SELECT s.EvrakTuru, s.SevkiyatNo, s.Tarih, u.UrunKodu, u.UrunAdi, idt.Miktar 
                FROM Sevkiyatlar s 
                JOIN Irsaliye_Detay idt ON idt.SevkiyatID = s.ID 
                JOIN Urunler u ON idt.UrunID = u.ID 
                WHERE s.SiparisID = ? 
                ORDER BY s.Tarih DESC
            """, (self.siparis_id,)).fetchall()

            self.tbl_gecmis.setRowCount(len(sevkler))
            for i, sv in enumerate(sevkler):
                self.tbl_gecmis.setItem(i, 0, QTableWidgetItem(str(sv['EvrakTuru'])))
                self.tbl_gecmis.setItem(i, 1, QTableWidgetItem(str(sv['SevkiyatNo'])))
                self.tbl_gecmis.setItem(i, 2, QTableWidgetItem(format_tarih_tr_saat(sv['Tarih'])))
                self.tbl_gecmis.setItem(i, 3, QTableWidgetItem(f"{sv['UrunKodu']} - {sv['UrunAdi']}"))
                
                it_m = QTableWidgetItem(f"{int(sv['Miktar']):,} Adet")
                it_m.setTextAlignment(Qt.AlignCenter)
                self.tbl_gecmis.setItem(i, 4, it_m)

    def save(self):
        if self.is_completed: return
        if self.table.rowCount() == 0 or not self.cmb_cari.currentText():
            return QMessageBox.warning(self, "Hata", "Lütfen geçerli bir cari ve en az bir sipariş kalemi girin!")

        c_txt = self.cmb_cari.currentText()
        c_id = self.cariler_map.get(c_txt, 1)
        s_no = self.txt_no.text().strip()
        s_tipi = self.cmb_tip.currentText()
        notlar = self.txt_notlar.toPlainText().strip()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        toplam_tutar = self.hesapla_toplam()

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            if self.siparis_id:
                cur.execute("UPDATE Siparisler SET SiparisNo=?, SiparisTipi=?, CariID=?, ToplamTutar=?, Aciklama=? WHERE ID=?",
                            (s_no, s_tipi, c_id, toplam_tutar, notlar, self.siparis_id))
                sp_id = self.siparis_id
            else:
                cur.execute("INSERT INTO Siparisler (SiparisNo, SiparisTipi, CariID, ToplamTutar, Durum, Tarih, Aciklama) VALUES (?, ?, ?, ?, 'Bekliyor', ?, ?)",
                            (s_no, s_tipi, c_id, toplam_tutar, now_str, notlar))
                sp_id = cur.lastrowid

            cur.execute("DELETE FROM Siparis_Detay WHERE SiparisID=?", (sp_id,))
            for r in range(self.table.rowCount()):
                cmb_u = self.table.cellWidget(r, 0)
                spn_m = self.table.cellWidget(r, 1)
                spn_f = self.table.cellWidget(r, 4)
                if cmb_u and spn_m and spn_f:
                    u = cmb_u.currentData()
                    if u and 'ID' in u:
                        cur.execute("INSERT INTO Siparis_Detay (SiparisID, UrunID, Miktar, SevkEdilen, BirimFiyat) VALUES (?, ?, ?, 0, ?)",
                                    (sp_id, u['ID'], spn_m.value(), spn_f.value()))

            conn.commit()

        QMessageBox.information(self, "Başarılı", "Sipariş bilgileri kaydedildi.")
        self.accept()

    def sevk_et(self):
        if self.is_completed or not self.siparis_id: return
        dlg_onay = SevkiyatOnayDialog(self)
        if dlg_onay.exec_() != QDialog.Accepted: return

        is_fatura_kes = dlg_onay.is_fatura()
        now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        evrak_no = f"{'FAT' if is_fatura_kes else 'IRS'}-{now_str}"
        suan_tarih = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        sevk_yapildi = False
        toplam_sevk_tutari = 0.0
        toplam_kdv = 0.0

        with self.db.get_connection() as conn:
            cur = conn.cursor()
            sp = cur.execute("SELECT CariID, SiparisTipi FROM Siparisler WHERE ID = ?", (self.siparis_id,)).fetchone()
            cari_id = row_get(sp, 'CariID', 0)
            s_tipi = row_get(sp, 'SiparisTipi', 'Müşteri')
            is_satis = "Müşteri" in s_tipi

            cur.execute("INSERT INTO Sevkiyatlar (SiparisID, EvrakTuru, SevkiyatNo, Tarih, CariID) VALUES (?, 'İrsaliye', ?, CURRENT_TIMESTAMP, ?)", (self.siparis_id, evrak_no, cari_id))
            sevk_id = cur.lastrowid

            for r in range(self.table.rowCount()):
                cmb_u = self.table.cellWidget(r, 0)
                spn_bu_sevk = self.table.cellWidget(r, 3)
                spn_f = self.table.cellWidget(r, 4)

                if cmb_u and spn_bu_sevk:
                    u = cmb_u.currentData()
                    d_id = cmb_u.property("detay_id")
                    gonderilecek = spn_bu_sevk.value()

                    if gonderilecek > 0:
                        sevk_yapildi = True
                        u_id = u['ID']
                        birim_fiyat = spn_f.value()
                        satir_tutari = gonderilecek * birim_fiyat
                        toplam_sevk_tutari += satir_tutari
                        toplam_kdv += satir_tutari * (float(u.get('KdvOrani', 20)) / 100.0)

                        if d_id: cur.execute("UPDATE Siparis_Detay SET SevkEdilen = COALESCE(SevkEdilen, 0) + ? WHERE ID = ?", (gonderilecek, d_id))
                        cur.execute("INSERT INTO Irsaliye_Detay (SevkiyatID, UrunID, Miktar, BirimFiyat) VALUES (?, ?, ?, ?)", (sevk_id, u_id, gonderilecek, birim_fiyat))

                        if is_satis: cur.execute("UPDATE Urunler SET Miktar = Miktar - ? WHERE ID = ?", (gonderilecek, u_id))
                        else: cur.execute("UPDATE Urunler SET Miktar = Miktar + ? WHERE ID = ?", (gonderilecek, u_id))

            if not sevk_yapildi: return QMessageBox.warning(self, "Hata", "Lütfen en az 1 miktar girin!")

            if is_fatura_kes:
                genel_toplam = toplam_sevk_tutari + toplam_kdv
                f_tipi = "Satış Faturası" if is_satis else "Alış Faturası"
                
                cur.execute("INSERT INTO Faturalar (FaturaNo, FaturaTipi, CariID, ToplamTutar, AraToplam, IskontoTutar, Masraf, KDVTutari, GenelToplam, Tarih, IrsaliyeNo) VALUES (?, ?, ?, ?, ?, 0, 0, ?, ?, ?, ?)",
                            (evrak_no, f_tipi, cari_id, toplam_sevk_tutari, toplam_sevk_tutari, toplam_kdv, genel_toplam, suan_tarih, evrak_no))
                
                if is_satis: cur.execute("UPDATE Cari_Hesaplar SET Bakiye = Bakiye + ? WHERE ID = ?", (genel_toplam, cari_id))
                else: cur.execute("UPDATE Cari_Hesaplar SET Bakiye = Bakiye - ? WHERE ID = ?", (genel_toplam, cari_id))

            detaylar = cur.execute("SELECT Miktar, SevkEdilen FROM Siparis_Detay WHERE SiparisID = ?", (self.siparis_id,)).fetchall()
            hepsi_bitti = all(row_get(d, 'SevkEdilen', 0) >= row_get(d, 'Miktar', 0) for d in detaylar)

            yeni_durum = "Tamamlandı" if hepsi_bitti else "Kısmi Sevk"
            cur.execute("UPDATE Siparisler SET Durum = ? WHERE ID = ?", (yeni_durum, self.siparis_id))

            conn.commit()

        QMessageBox.information(self, "Başarılı", f"Sevkiyat Yapıldı ({evrak_no}). Sipariş Durumu: {yeni_durum}")
        self.accept()

class SiparisWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        l = QVBoxLayout(self)
        grp = QGroupBox("🛒 Müşteri & Tedarikçi Sipariş Yönetimi")
        grp.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        v = QVBoxLayout(grp)

        btn_bar = QHBoxLayout()
        btn_yeni = QPushButton("➕ Yeni Sipariş Oluştur")
        btn_yeni.setProperty("btnClass", "success")
        btn_yeni.clicked.connect(self.open_yeni)

        btn_inc = QPushButton("👁️ Sipariş Detayı & Sevkiyat Yap")
        btn_inc.setProperty("btnClass", "primary")
        btn_inc.clicked.connect(self.open_inc)

        btn_bar.addWidget(btn_yeni)
        btn_bar.addWidget(btn_inc)
        btn_bar.addStretch()
        v.addLayout(btn_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(7)
        self.table.setHorizontalHeaderLabels(["ID", "Sipariş Türü", "Sipariş No", "Cari Firma Ünvanı", "Tarih & Saat", "Toplam Tutar (₺)", "Durum"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        header = self.table.horizontalHeader()
        for c in range(7): header.setSectionResizeMode(c, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(40)

        self.table.doubleClicked.connect(self.open_inc)
        v.addWidget(self.table)
        l.addWidget(grp)

    def load_data(self):
        with self.db.get_connection() as conn:
            siparisler = conn.execute("""
                SELECT sp.*, c.Unvan 
                FROM Siparisler sp 
                JOIN Cari_Hesaplar c ON sp.CariID = c.ID 
                ORDER BY sp.ID DESC
            """).fetchall()
            self.table.setRowCount(len(siparisler))
            for i, s in enumerate(siparisler):
                self.table.setItem(i, 0, QTableWidgetItem(str(row_get(s, 'ID', ''))))
                self.table.setItem(i, 1, QTableWidgetItem(str(row_get(s, 'SiparisTipi', 'Müşteri Siparişi'))))
                self.table.setItem(i, 2, QTableWidgetItem(str(row_get(s, 'SiparisNo', ''))))
                self.table.setItem(i, 3, QTableWidgetItem(str(row_get(s, 'Unvan', ''))))
                self.table.setItem(i, 4, QTableWidgetItem(format_tarih_tr_saat(row_get(s, 'Tarih', ''))))
                self.table.setItem(i, 5, QTableWidgetItem(f"₺ {float(row_get(s, 'ToplamTutar', 0.0)):,.2f}"))

                durum = str(row_get(s, 'Durum', 'Bekliyor'))
                it_d = QTableWidgetItem(durum)
                it_d.setTextAlignment(Qt.AlignCenter)
                if durum == 'Tamamlandı':
                    it_d.setBackground(QColor("#27ae60")); it_d.setForeground(QColor("white"))
                elif durum == 'Kısmi Sevk':
                    it_d.setBackground(QColor("#2980b9")); it_d.setForeground(QColor("white"))
                else:
                    it_d.setBackground(QColor("#d35400")); it_d.setForeground(QColor("white"))

                self.table.setItem(i, 6, it_d)

    def open_yeni(self):
        if SiparisDialog(self, self.db).exec_() == QDialog.Accepted: self.load_data()

    def open_inc(self):
        r = self.table.currentRow()
        if r < 0: return QMessageBox.warning(self, "Hata", "Lütfen bir sipariş seçin!")
        sp_id = int(self.table.item(r, 0).text())
        if SiparisDialog(self, self.db, sp_id).exec_() == QDialog.Accepted: self.load_data()