# C:\Gmn_Muhasebe\moduller\ui\stok_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QHeaderView, QDialog, QMessageBox, QTabWidget, QAbstractItemView,
    QLabel, QLineEdit, QCheckBox, QComboBox
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from moduller.services.stok_service import StokService
from moduller.ui.styles import SafeSpinBox, SafeDoubleSpinBox

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
    except Exception:
        return str(tarih_str)

class StokDetayDialog(QDialog):
    def __init__(self, parent, db, urun_data=None):
        super().__init__(parent)
        self.db = db
        self.urun_data = urun_data or {}
        self.stok_service = StokService(db)
        title = f"📦 Stok İncele & Düzenle: {self.urun_data.get('UrunKodu', '')}" if self.urun_data.get('ID') else "➕ Yeni Stok / Reçeteli Ürün Ekle"
        self.setWindowTitle(title)
        self.resize(1150, 780)
        self.setup_ui()

    def setup_ui(self):
        l = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # TAB 1: Ürün Kart Bilgileri
        w_kart = QWidget()
        l_k = QVBoxLayout(w_kart)

        self.txt_kodu = QLineEdit(self.urun_data.get('UrunKodu', ''))
        self.txt_adi = QLineEdit(self.urun_data.get('UrunAdi', ''))
        self.spn_maliyet = SafeDoubleSpinBox(); self.spn_maliyet.setRange(0, 999999); self.spn_maliyet.setValue(float(self.urun_data.get('Maliyet', 0.0) or 0.0))
        self.spn_satis = SafeDoubleSpinBox(); self.spn_satis.setRange(0, 999999); self.spn_satis.setValue(float(self.urun_data.get('SatisFiyati', 0.0) or 0.0))
        self.spn_kdv = SafeSpinBox(); self.spn_kdv.setRange(0, 100); self.spn_kdv.setValue(int(self.urun_data.get('KdvOrani', 20) or 20))
        self.spn_miktar = SafeDoubleSpinBox(); self.spn_miktar.setRange(0, 999999); self.spn_miktar.setValue(float(self.urun_data.get('Miktar', 0.0) or 0.0))
        
        self.chk_paket = QCheckBox("📦 Bu Ürün Reçeteli Paket / Tamir Takımıdır")
        self.chk_paket.setChecked(bool(self.urun_data.get('IsPaket', 0)))
        self.chk_paket.toggled.connect(self.toggle_paket_tab)

        l_k.addWidget(QLabel("Stok Kodu:")); l_k.addWidget(self.txt_kodu)
        l_k.addWidget(QLabel("Stok Adı:")); l_k.addWidget(self.txt_adi)
        l_k.addWidget(QLabel("Alış Maliyeti / Giriş Fiyatı (₺):")); l_k.addWidget(self.spn_maliyet)
        l_k.addWidget(QLabel("Satış Fiyatı (₺):")); l_k.addWidget(self.spn_satis)
        l_k.addWidget(QLabel("KDV Oranı (%):")); l_k.addWidget(self.spn_kdv)
        l_k.addWidget(QLabel("Stok Miktarı (Adet):")); l_k.addWidget(self.spn_miktar)
        l_k.addWidget(self.chk_paket)

        btn_save = QPushButton("💾 Stok Kartını Kaydet / Güncelle")
        btn_save.setProperty("btnClass", "success")
        btn_save.clicked.connect(self.save)
        l_k.addWidget(btn_save)
        self.tabs.addTab(w_kart, "Kart Bilgileri")

        # TAB 2: Reçete / Paket İçeriği
        self.w_recete = QWidget()
        l_r = QVBoxLayout(self.w_recete)
        
        btn_alt_ekle = QPushButton("+ Alt Parça / Eleman Ekle")
        btn_alt_ekle.setProperty("btnClass", "primary")
        btn_alt_ekle.clicked.connect(self.add_recete_row)
        l_r.addWidget(btn_alt_ekle, alignment=Qt.AlignLeft)

        self.tbl_recete = QTableWidget()
        self.tbl_recete.setColumnCount(4)
        self.tbl_recete.setHorizontalHeaderLabels(["Alt Ürün / Parça", "Birim Miktar", "Birim Maliyet (₺)", "İşlem"])
        self.tbl_recete.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        l_r.addWidget(self.tbl_recete)

        self.lbl_recete_maliyet = QLabel("<b>Hesaplanan Reçete Toplam Maliyeti: ₺ 0.00</b>")
        self.lbl_recete_maliyet.setStyleSheet("font-size:11pt; color:#c0392b;")
        l_r.addWidget(self.lbl_recete_maliyet, alignment=Qt.AlignRight)

        self.tabs.addTab(self.w_recete, "Reçete / Paket İçeriği")

        # TAB 3: Stok Hareket Föyü
        if self.urun_data.get('ID'):
            w_foy = QWidget()
            l_f = QVBoxLayout(w_foy)
            self.tbl_foy = QTableWidget()
            self.tbl_foy.setColumnCount(5)
            self.tbl_foy.setHorizontalHeaderLabels(["Evrak Türü", "Evrak No", "Tarih & Saat", "Miktar", "Birim Fiyat (₺)"])
            self.tbl_foy.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tbl_foy.setSelectionBehavior(QAbstractItemView.SelectRows)
            
            self.tbl_foy.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.tbl_foy.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
            self.tbl_foy.horizontalHeader().setSectionResizeMode(2, QHeaderView.ResizeToContents)
            self.tbl_foy.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
            self.tbl_foy.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)

            self.tbl_foy.doubleClicked.connect(self.open_fatura_dokum)
            l_f.addWidget(self.tbl_foy)
            self.tabs.addTab(w_foy, "Stok Hareket Föyü (Çift Tıkla: Evrak Detayı)")
            self.load_foy()

        l.addWidget(self.tabs)
        self.toggle_paket_tab(self.chk_paket.isChecked())
        if self.urun_data.get('ID'): self.load_recete()

    def toggle_paket_tab(self, checked):
        self.tabs.setTabEnabled(1, checked)
        if checked:
            self.spn_maliyet.setReadOnly(True)

    def load_recete(self):
        recete = self.stok_service.get_recete_elemanlari(self.urun_data['ID'])
        self.tbl_recete.setRowCount(0)
        for r in recete:
            self.add_recete_row(r['AltUrunID'], r['Miktar'], r['Maliyet'])
        self.hesapla_recete_maliyeti()

    def add_recete_row(self, alt_id=None, miktar=1.0, birim_maliyet=0.0):
        row = self.tbl_recete.rowCount()
        self.tbl_recete.insertRow(row)

        alt_urunler = self.stok_service.get_tum_alt_urunler(self.urun_data.get('ID'))
        cmb = QComboBox()
        for u in alt_urunler:
            cmb.addItem(f"{u['UrunKodu']} - {u['UrunAdi']}", dict(u))
            if alt_id and u['ID'] == alt_id:
                cmb.setCurrentIndex(cmb.count() - 1)

        spn_m = SafeDoubleSpinBox(); spn_m.setRange(0.01, 9999); spn_m.setValue(float(miktar)); spn_m.valueChanged.connect(self.hesapla_recete_maliyeti)
        lbl_m = QLabel(f"₺ {float(birim_maliyet):,.2f}")
        
        btn_del = QPushButton("❌")
        btn_del.setProperty("btnClass", "danger")
        btn_del.clicked.connect(lambda: (self.tbl_recete.removeRow(self.tbl_recete.currentRow()), self.hesapla_recete_maliyeti()))

        self.tbl_recete.setCellWidget(row, 0, cmb)
        self.tbl_recete.setCellWidget(row, 1, spn_m)
        self.tbl_recete.setCellWidget(row, 2, lbl_m)
        self.tbl_recete.setCellWidget(row, 3, btn_del)

        cmb.currentIndexChanged.connect(lambda: self.alt_urun_secildi(row, cmb))
        if not alt_id and alt_urunler: self.alt_urun_secildi(row, cmb)
        self.hesapla_recete_maliyeti()

    def alt_urun_secildi(self, row, cmb):
        u = cmb.currentData()
        if u:
            self.tbl_recete.cellWidget(row, 2).setText(f"₺ {float(u.get('Maliyet', 0.0)):,.2f}")
        self.hesapla_recete_maliyeti()

    def hesapla_recete_maliyeti(self):
        tot_maliyet = 0.0
        for r in range(self.tbl_recete.rowCount()):
            cmb = self.tbl_recete.cellWidget(r, 0)
            spn = self.tbl_recete.cellWidget(r, 1)
            if cmb and spn:
                u = cmb.currentData()
                if u:
                    tot_maliyet += float(u.get('Maliyet', 0.0)) * spn.value()
        self.lbl_recete_maliyet.setText(f"<b>Hesaplanan Reçete Toplam Maliyeti: ₺ {tot_maliyet:,.2f}</b>")
        if self.chk_paket.isChecked():
            self.spn_maliyet.setValue(tot_maliyet)

    def load_foy(self):
        foyler = self.stok_service.get_stok_hareket_foyler(self.urun_data['ID'])
        self.tbl_foy.setRowCount(len(foyler))
        for i, f in enumerate(foyler):
            evrak_turu = str(f['EvrakTuru'])
            aciklama = str(f['Aciklama'] or '')

            it_e = QTableWidgetItem(f"{evrak_turu} ({aciklama})" if aciklama else evrak_turu)
            
            if "Alış" in aciklama or "Giriş" in aciklama:
                it_e.setBackground(QColor("#27ae60")); it_e.setForeground(QColor("white"))
            elif "Montaj" in aciklama or "İmalat" in aciklama:
                it_e.setBackground(QColor("#8e44ad")); it_e.setForeground(QColor("white"))
            else:
                it_e.setBackground(QColor("#2980b9")); it_e.setForeground(QColor("white"))

            self.tbl_foy.setItem(i, 0, it_e)
            self.tbl_foy.setItem(i, 1, QTableWidgetItem(str(f['EvrakNo'])))
            self.tbl_foy.setItem(i, 2, QTableWidgetItem(format_tarih_tr_saat(f['Tarih'])))
            
            it_m = QTableWidgetItem(f"{int(f['Miktar']):,} Adet")
            it_m.setTextAlignment(Qt.AlignCenter)
            self.tbl_foy.setItem(i, 3, it_m)

            it_f = QTableWidgetItem(f"₺ {f['BirimFiyat']:,.2f}")
            it_f.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
            self.tbl_foy.setItem(i, 4, it_f)

    def open_fatura_dokum(self):
        r = self.tbl_foy.currentRow()
        if r < 0: return
        evrak_no = self.tbl_foy.item(r, 1).text()
        evrak_turu = self.tbl_foy.item(r, 0).text()
        
        from moduller.ui.fatura_ui import FaturaDokumDialog
        FaturaDokumDialog(self, self.db, evrak_no, evrak_turu).exec_()

    def save(self):
        kodu = self.txt_kodu.text().strip()
        adi = self.txt_adi.text().strip()
        if not kodu or not adi:
            return QMessageBox.warning(self, "Hata", "Stok Kodu ve Adı boş bırakılamaz!")

        recete_list = []
        if self.chk_paket.isChecked():
            for r in range(self.tbl_recete.rowCount()):
                cmb = self.tbl_recete.cellWidget(r, 0)
                spn = self.tbl_recete.cellWidget(r, 1)
                if cmb and spn:
                    u = cmb.currentData()
                    if u and 'ID' in u:
                        recete_list.append({'alt_urun_id': u['ID'], 'miktar': spn.value()})

        u_data = {
            'id': self.urun_data.get('ID'),
            'urun_kodu': kodu,
            'urun_adi': adi,
            'maliyet': self.spn_maliyet.value(),
            'satis_fiyati': self.spn_satis.value(),
            'kdv_orani': self.spn_kdv.value(),
            'miktar': self.spn_miktar.value(),
            'is_paket': 1 if self.chk_paket.isChecked() else 0
        }

        try:
            self.stok_service.urun_ekle_veya_guncelle(u_data, recete_list)
            QMessageBox.information(self, "Başarılı", "Stok kartı ve reçete başarıyla kaydedildi.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Stok kaydı sırasında hata: {str(e)}")

class StokWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        l = QVBoxLayout(self)
        grp = QGroupBox("📦 Stok / Ürün Yönetimi & Tamir Takımları (Reçeteler)")
        grp.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        v = QVBoxLayout(grp)

        btn_bar = QHBoxLayout()
        btn_yeni = QPushButton("➕ Yeni Stok / Reçeteli Paket Kartı")
        btn_yeni.setProperty("btnClass", "success")
        btn_yeni.clicked.connect(self.open_yeni_stok)

        btn_inc = QPushButton("👁️ Stok Kartı & Reçete İncele")
        btn_inc.setProperty("btnClass", "primary")
        btn_inc.clicked.connect(self.open_inc)

        btn_bar.addWidget(btn_yeni)
        btn_bar.addWidget(btn_inc)
        btn_bar.addStretch()
        v.addLayout(btn_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Stok Kodu", "Ürün / Paket Adı", "Ürün Türü", "Depo Miktarı", "Alış Maliyeti", "Satış Fiyatı", "KDV %"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        # Dengeli Çift Yönlü Sütun Hizalaması
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.horizontalHeader().setSectionResizeMode(3, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(4, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(5, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(6, QHeaderView.ResizeToContents)
        self.table.horizontalHeader().setSectionResizeMode(7, QHeaderView.ResizeToContents)

        self.table.doubleClicked.connect(self.open_inc)
        v.addWidget(self.table)
        l.addWidget(grp)

    def load_data(self):
        with self.db.get_connection() as conn:
            urunler = conn.execute("SELECT * FROM Urunler ORDER BY ID DESC").fetchall()
            self.table.setRowCount(len(urunler))
            for i, u in enumerate(urunler):
                self.table.setItem(i, 0, QTableWidgetItem(str(u['ID'])))
                self.table.setItem(i, 1, QTableWidgetItem(str(u['UrunKodu'] or '')))
                self.table.setItem(i, 2, QTableWidgetItem(str(u['UrunAdi'] or '')))
                
                is_p = u['IsPaket'] if 'IsPaket' in u.keys() and u['IsPaket'] else 0
                it_p = QTableWidgetItem("📦 Reçeteli Paket" if is_p == 1 else "📄 Standart Ürün")
                self.table.setItem(i, 3, it_p)

                mikt = u['Miktar'] if 'Miktar' in u.keys() and u['Miktar'] is not None else 0.0
                it_m = QTableWidgetItem(f"{int(mikt):,} Adet")
                it_m.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 4, it_m)

                maliyet = u['Maliyet'] if 'Maliyet' in u.keys() and u['Maliyet'] is not None else 0.0
                it_mal = QTableWidgetItem(f"₺ {maliyet:,.2f}")
                it_mal.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, 5, it_mal)

                satis = u['SatisFiyati'] if 'SatisFiyati' in u.keys() and u['SatisFiyati'] is not None else 0.0
                it_sat = QTableWidgetItem(f"₺ {satis:,.2f}")
                it_sat.setTextAlignment(Qt.AlignRight | Qt.AlignVCenter)
                self.table.setItem(i, 6, it_sat)

                kdv = u['KdvOrani'] if 'KdvOrani' in u.keys() and u['KdvOrani'] is not None else 20
                it_k = QTableWidgetItem(f"%{int(kdv)}")
                it_k.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(i, 7, it_k)

    def open_yeni_stok(self):
        if StokDetayDialog(self, self.db).exec_() == QDialog.Accepted:
            self.load_data()

    def open_inc(self):
        r = self.table.currentRow()
        if r < 0: return QMessageBox.warning(self, "Hata", "Lütfen bir stok kartı seçin!")
        u_id = int(self.table.item(r, 0).text())
        with self.db.get_connection() as conn:
            u_data = conn.execute("SELECT * FROM Urunler WHERE ID=?", (u_id,)).fetchone()
            if u_data and StokDetayDialog(self, self.db, dict(u_data)).exec_() == QDialog.Accepted:
                self.load_data()