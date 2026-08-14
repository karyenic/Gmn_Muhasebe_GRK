# C:\Gmn_Muhasebe\moduller\ui\finans_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QHeaderView, QDialog, QMessageBox, QLabel,
    QLineEdit, QComboBox, QDoubleSpinBox, QTextEdit, QAbstractItemView
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from moduller.services.finans_service import FinansService

class SafeDoubleSpinBox(QDoubleSpinBox):
    def wheelEvent(self, event):
        event.ignore()

def format_tarih_tr_saat(tarih_str):
    if not tarih_str: return ""
    try:
        if " " in tarih_str:
            t_parca, s_parca = tarih_str.split(" ")
            y, m, d = t_parca.split("-")
            s_parca = ":".join(s_parca.split(":")[:2])
            return f"{d}/{m}/{y} {s_parca}"
        else:
            y, m, d = tarih_str.split("-")
            return f"{d}/{m}/{y}"
    except Exception:
        return str(tarih_str)

class KasaIslemDialog(QDialog):
    def __init__(self, parent, db, islem_turu="Tahsilat"):
        super().__init__(parent)
        self.db = db
        self.islem_turu = islem_turu
        self.finans_service = FinansService(db)
        self.setWindowTitle(f"💵 Kasa {islem_turu} Fişi Düzenle")
        self.resize(550, 400)
        self.setup_ui()
        self.load_cariler()

    def setup_ui(self):
        l = QVBoxLayout(self)

        l.addWidget(QLabel(f"<b>İşlem Türü:</b> {self.islem_turu}"))

        self.cmb_cari = QComboBox()
        l.addWidget(QLabel("Cari / Müşteri / Tedarikçi Seçin:"))
        l.addWidget(self.cmb_cari)

        self.spn_tutar = SafeDoubleSpinBox()
        self.spn_tutar.setRange(0.01, 9999999.0)
        self.spn_tutar.setValue(0.0)
        l.addWidget(QLabel("Tutar (₺):"))
        l.addWidget(self.spn_tutar)

        self.txt_aciklama = QTextEdit()
        self.txt_aciklama.setMaximumHeight(80)
        l.addWidget(QLabel("Açıklama / Fiş Notu:"))
        l.addWidget(self.txt_aciklama)

        btn_kaydet = QPushButton(f"💾 {self.islem_turu} Kaydet")
        bg_color = "#27ae60" if self.islem_turu == "Tahsilat" else "#c0392b"
        btn_kaydet.setStyleSheet(f"background-color: {bg_color}; color: white; font-weight: bold; padding: 12px;")
        btn_kaydet.clicked.connect(self.save)
        l.addWidget(btn_kaydet)

    def load_cariler(self):
        self.cariler_map = {}
        with self.db.get_connection() as conn:
            cariler = conn.execute("SELECT ID, CariKodu, Unvan FROM Cari_Hesaplar WHERE Durum != 'Pasif' ORDER BY Unvan ASC").fetchall()
            for c in cariler:
                lbl = f"{c['CariKodu']} - {c['Unvan']}"
                self.cariler_map[lbl] = c['ID']
                self.cmb_cari.addItem(lbl)

    def save(self):
        if self.cmb_cari.currentText() not in self.cariler_map:
            return QMessageBox.warning(self, "Hata", "Lütfen geçerli bir cari seçin!")

        tutar = self.spn_tutar.value()
        if tutar <= 0:
            return QMessageBox.warning(self, "Hata", "Tutar 0'dan büyük olmalıdır!")

        c_id = self.cariler_map[self.cmb_cari.currentText()]
        aciklama = self.txt_aciklama.toPlainText().strip()

        try:
            self.finans_service.kasa_islemi_ekle(c_id, self.islem_turu, tutar, aciklama)
            QMessageBox.information(self, "Başarılı", f"Kasa {self.islem_turu} işlemi başarıyla kaydedildi.")
            self.accept()
        except Exception as e:
            QMessageBox.critical(self, "Hata", f"İşlem kaydedilirken hata oluştu: {str(e)}")

class FinansWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.finans_service = FinansService(db_manager)
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        l = QVBoxLayout(self)
        grp = QGroupBox("💰 Finans & Kasa Yönetimi")
        grp.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        v = QVBoxLayout(grp)

        btn_bar = QHBoxLayout()
        btn_tahsilat = QPushButton("📥 Kasa Tahsilat Fişi (Giriş)")
        btn_tahsilat.setStyleSheet("background-color: #27ae60; color: white; padding: 10px 15px; font-weight: bold;")
        btn_tahsilat.clicked.connect(lambda: self.open_islem_dialog("Tahsilat"))

        btn_tediye = QPushButton("📤 Kasa Tediye Fişi (Çıkış/Ödeme)")
        btn_tediye.setStyleSheet("background-color: #c0392b; color: white; padding: 10px 15px; font-weight: bold;")
        btn_tediye.clicked.connect(lambda: self.open_islem_dialog("Tediye"))

        btn_bar.addWidget(btn_tahsilat)
        btn_bar.addWidget(btn_tediye)
        btn_bar.addStretch()
        v.addLayout(btn_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["ID", "İşlem Türü", "Cari Ünvan", "Tarih & Saat", "Tutar (₺)", "Açıklama"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setSectionResizeMode(2, QHeaderView.Stretch)
        v.addWidget(self.table)

        l.addWidget(grp)

    def load_data(self):
        hareketler = self.finans_service.get_kasa_hareketleri()
        self.table.setRowCount(len(hareketler))
        for i, h in enumerate(hareketler):
            self.table.setItem(i, 0, QTableWidgetItem(str(h['ID'])))
            
            it_t = QTableWidgetItem(h['IslemTuru'])
            if h['IslemTuru'] == 'Tahsilat':
                it_t.setBackground(QColor("#27ae60")); it_t.setForeground(QColor("white"))
            else:
                it_t.setBackground(QColor("#c0392b")); it_t.setForeground(QColor("white"))
            self.table.setItem(i, 1, it_t)

            self.table.setItem(i, 2, QTableWidgetItem(str(h['Unvan'] or '')))
            self.table.setItem(i, 3, QTableWidgetItem(format_tarih_tr_saat(h['Tarih'])))
            self.table.setItem(i, 4, QTableWidgetItem(f"₺ {h['Tutar']:,.2f}"))
            self.table.setItem(i, 5, QTableWidgetItem(str(h['Aciklama'] or '')))

    def open_islem_dialog(self, islem_turu):
        if KasaIslemDialog(self, self.db, islem_turu).exec_() == QDialog.Accepted:
            self.load_data()