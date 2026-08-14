# C:\Gmn_Muhasebe\moduller\ui\cari_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QHeaderView, QDialog, QMessageBox, QTabWidget, QAbstractItemView,
    QLabel, QLineEdit, QTextEdit
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from moduller.services.cari_service import CariService

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

class CariKartDialog(QDialog):
    def __init__(self, parent, db, cari_id=None):
        super().__init__(parent)
        self.db = db
        self.cari_id = cari_id
        self.cari_service = CariService(db)
        self.setWindowTitle("👁️ Cari Hesap Kartı & Ekstre" if cari_id else "➕ Yeni Cari Hesap Kartı")
        self.resize(1100, 750)
        self.setup_ui()
        if self.cari_id:
            self.load_cari_data()
            self.load_ekstre()

    def setup_ui(self):
        l = QVBoxLayout(self)
        self.tabs = QTabWidget()

        # TAB 1: Cari Kart Bilgileri
        w_kart = QWidget()
        l_k = QVBoxLayout(w_kart)

        self.txt_kodu = QLineEdit()
        self.txt_unvan = QLineEdit()
        self.txt_yetkili = QLineEdit()
        self.txt_telefon = QLineEdit()
        self.txt_eposta = QLineEdit()
        self.txt_vergi_d = QLineEdit()
        self.txt_vergi_n = QLineEdit()
        self.txt_adres = QTextEdit(); self.txt_adres.setMaximumHeight(60)

        l_k.addWidget(QLabel("Cari Kodu:")); l_k.addWidget(self.txt_kodu)
        l_k.addWidget(QLabel("Cari Ünvanı / Firma Adı:")); l_k.addWidget(self.txt_unvan)
        
        h_y = QHBoxLayout()
        h_y.addWidget(QLabel("Yetkili Kişi:")); h_y.addWidget(self.txt_yetkili)
        h_y.addWidget(QLabel("Telefon:")); h_y.addWidget(self.txt_telefon)
        l_k.addLayout(h_y)

        h_v = QHBoxLayout()
        h_v.addWidget(QLabel("E-Posta:")); h_v.addWidget(self.txt_eposta)
        h_v.addWidget(QLabel("Vergi Dairesi:")); h_v.addWidget(self.txt_vergi_d)
        h_v.addWidget(QLabel("Vergi No / TC:")); h_v.addWidget(self.txt_vergi_n)
        l_k.addLayout(h_v)

        l_k.addWidget(QLabel("Açık Adres:")); l_k.addWidget(self.txt_adres)

        btn_save = QPushButton("💾 Cari Kartını Kaydet / Güncelle")
        btn_save.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 12px;")
        btn_save.clicked.connect(self.save)
        l_k.addWidget(btn_save)

        self.tabs.addTab(w_kart, "Cari Kart Bilgileri")

        # TAB 2: Cari Ekstre / Yürüyen Bakiye
        if self.cari_id:
            w_eks = QWidget()
            l_e = QVBoxLayout(w_eks)

            self.tbl_ekstre = QTableWidget()
            self.tbl_ekstre.setColumnCount(6)
            self.tbl_ekstre.setHorizontalHeaderLabels(["Evrak Türü", "Evrak No", "Tarih", "Borç (₺)", "Alacak (₺)", "Bakiye (₺)"])
            self.tbl_ekstre.setEditTriggers(QAbstractItemView.NoEditTriggers)
            self.tbl_ekstre.setSelectionBehavior(QAbstractItemView.SelectRows)
            self.tbl_ekstre.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
            self.tbl_ekstre.doubleClicked.connect(self.open_fatura_dokum)
            l_e.addWidget(self.tbl_ekstre)

            self.lbl_bakiye_ozet = QLabel("<b>Net Bakiye: ₺ 0.00</b>")
            self.lbl_bakiye_ozet.setStyleSheet("font-size: 13pt; padding: 5px;")
            l_e.addWidget(self.lbl_bakiye_ozet, alignment=Qt.AlignRight)

            self.tabs.addTab(w_eks, "Cari Ekstre / Yürüyen Bakiye (Çift Tıkla: Fatura)")

        l.addWidget(self.tabs)

    def load_cari_data(self):
        c = self.cari_service.get_cari_by_id(self.cari_id)
        if c:
            self.txt_kodu.setText(c['CariKodu'])
            self.txt_unvan.setText(c['Unvan'])
            self.txt_yetkili.setText(c['YetkiliKisi'] or '')
            self.txt_telefon.setText(c['Telefon'] or '')
            self.txt_eposta.setText(c['Eposta'] or '')
            self.txt_vergi_d.setText(c['VergiDairesi'] or '')
            self.txt_vergi_n.setText(c['VergiNo'] or '')
            self.txt_adres.setText(c['Adres'] or '')

    def load_ekstre(self):
        ekstre = self.cari_service.get_cari_ekstre(self.cari_id)
        self.tbl_ekstre.setRowCount(len(ekstre))
        
        yuruyen_bakiye = 0.0
        for i, h in enumerate(ekstre):
            evrak_turu = h['EvrakTuru']
            borc = float(h['Borc'] or 0.0)
            alacak = float(h['Alacak'] or 0.0)
            
            yuruyen_bakiye += (borc - alacak)

            it_e = QTableWidgetItem(evrak_turu)
            
            if "Alış Faturası" in evrak_turu:
                it_e.setBackground(QColor("#8e44ad")); it_e.setForeground(QColor("white"))
            elif "Satış Faturası" in evrak_turu:
                it_e.setBackground(QColor("#27ae60")); it_e.setForeground(QColor("white"))
            elif "Tahsilat" in evrak_turu:
                it_e.setBackground(QColor("#2980b9")); it_e.setForeground(QColor("white"))
            elif "Tediye" in evrak_turu:
                it_e.setBackground(QColor("#d35400")); it_e.setForeground(QColor("white"))
            
            self.tbl_ekstre.setItem(i, 0, it_e)
            self.tbl_ekstre.setItem(i, 1, QTableWidgetItem(str(h['EvrakNo'] or '')))
            self.tbl_ekstre.setItem(i, 2, QTableWidgetItem(format_tarih_tr_saat(h['Tarih'])))
            
            it_borc = QTableWidgetItem(f"₺ {borc:,.2f}")
            if borc > 0: it_borc.setForeground(QColor("#27ae60"))
            self.tbl_ekstre.setItem(i, 3, it_borc)

            it_alacak = QTableWidgetItem(f"₺ {alacak:,.2f}")
            if alacak > 0: it_alacak.setForeground(QColor("#c0392b"))
            self.tbl_ekstre.setItem(i, 4, it_alacak)

            it_bak = QTableWidgetItem(f"₺ {yuruyen_bakiye:,.2f}")
            if yuruyen_bakiye < 0:
                it_bak.setForeground(QColor("#c0392b"))
            elif yuruyen_bakiye > 0:
                it_bak.setForeground(QColor("#27ae60"))
            self.tbl_ekstre.setItem(i, 5, it_bak)

        bakiye_metin = f"<b>Net Bakiye: ₺ {yuruyen_bakiye:,.2f} ({'Borçlu / Müşteri Borçlu' if yuruyen_bakiye > 0 else 'Alacaklı / Tedarikçi Alacaklı'})</b>"
        bakiye_renk = "#27ae60" if yuruyen_bakiye > 0 else ("#c0392b" if yuruyen_bakiye < 0 else "#2c3e50")
        self.lbl_bakiye_ozet.setText(bakiye_metin)
        self.lbl_bakiye_ozet.setStyleSheet(f"font-size: 12pt; color: {bakiye_renk}; font-weight: bold; padding: 5px;")

    def open_fatura_dokum(self):
        r = self.tbl_ekstre.currentRow()
        if r < 0: return
        evrak_no = self.tbl_ekstre.item(r, 1).text()
        evrak_turu = self.tbl_ekstre.item(r, 0).text()
        
        with self.db.get_connection() as conn:
            fat = conn.execute("SELECT ID FROM Faturalar WHERE FaturaNo = ?", (evrak_no,)).fetchone()
            if fat:
                # Dinamik Import (Dairesel bağımlılığı önler)
                from moduller.ui.fatura_ui import FaturaDokumDialog
                FaturaDokumDialog(self, self.db, fat['ID'], evrak_turu).exec_()

    def save(self):
        kodu = self.txt_kodu.text().strip()
        unvan = self.txt_unvan.text().strip()

        if not kodu or not unvan:
            return QMessageBox.warning(self, "Hata", "Cari Kodu ve Ünvanı boş bırakılamaz!")

        c_data = {
            'id': self.cari_id,
            'cari_kodu': kodu,
            'unvan': unvan,
            'yetkili_kisi': self.txt_yetkili.text().strip(),
            'telefon': self.txt_telefon.text().strip(),
            'eposta': self.txt_eposta.text().strip(),
            'vergi_dairesi': self.txt_vergi_d.text().strip(),
            'vergi_no': self.txt_vergi_n.text().strip(),
            'adres': self.txt_adres.toPlainText().strip()
        }

        try:
            self.cari_service.cari_ekle_veya_guncelle(c_data)
            QMessageBox.information(self, "Başarılı", "Cari kart bilgileri kaydedildi.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"Cari kaydı hatası: {str(e)}")

class CariWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.cari_service = CariService(db_manager)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        l = QVBoxLayout(self)
        grp = QGroupBox("👥 Cari Hesaplar Yönetimi")
        grp.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        v = QVBoxLayout(grp)

        btn_bar = QHBoxLayout()
        btn_yeni = QPushButton("➕ Yeni Cari Hesap Kartı")
        btn_yeni.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 10px 15px;")
        btn_yeni.clicked.connect(self.open_yeni_cari)

        btn_inc = QPushButton("👁️ Cari Kart & Ekstre İncele")
        btn_inc.setStyleSheet("background-color: #2980b9; color: white; font-weight: bold; padding: 10px 15px;")
        btn_inc.clicked.connect(self.open_inc)

        btn_bar.addWidget(btn_yeni)
        btn_bar.addWidget(btn_inc)
        btn_bar.addStretch()
        v.addLayout(btn_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "Cari Kodu", "Firma Ünvanı", "Telefon", "Vergi No", "Net Bakiye (₺)"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        self.table.doubleClicked.connect(self.open_inc)
        v.addWidget(self.table)

        l.addWidget(grp)

    def load_data(self):
        cariler = self.cari_service.get_tum_cariler()
        self.table.setRowCount(len(cariler))
        for i, c in enumerate(cariler):
            self.table.setItem(i, 0, QTableWidgetItem(str(c['ID'])))
            self.table.setItem(i, 1, QTableWidgetItem(c['CariKodu']))
            self.table.setItem(i, 2, QTableWidgetItem(c['Unvan']))
            self.table.setItem(i, 3, QTableWidgetItem(str(c['Telefon'] or '')))
            self.table.setItem(i, 4, QTableWidgetItem(str(c['VergiNo'] or '')))

            bak = float(c['Bakiye'] or 0.0)
            it_bak = QTableWidgetItem(f"₺ {bak:,.2f}")
            if bak < 0:
                it_bak.setForeground(QColor("#c0392b"))
            elif bak > 0:
                it_bak.setForeground(QColor("#27ae60"))
            self.table.setItem(i, 5, it_bak)

    def open_yeni_cari(self):
        if CariKartDialog(self, self.db).exec_() == QDialog.Accepted:
            self.load_data()

    def open_inc(self):
        r = self.table.currentRow()
        if r < 0: return QMessageBox.warning(self, "Hata", "Lütfen bir cari kart seçin!")
        c_id = int(self.table.item(r, 0).text())
        if CariKartDialog(self, self.db, c_id).exec_() == QDialog.Accepted:
            self.load_data()