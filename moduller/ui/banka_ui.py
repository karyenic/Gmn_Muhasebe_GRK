import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, 
    QTableWidgetItem, QPushButton, QGroupBox, QHeaderView,
    QLabel, QLineEdit, QComboBox, QDoubleSpinBox, QMessageBox, QCompleter, QDialog
)
from PyQt5.QtCore import Qt
from moduller.database.db_manager import DBManager

class FinansIslemDialog(QDialog):
    def __init__(self, parent, db_manager: DBManager, islem_turu="Tahsilat"):
        super().__init__(parent)
        self.db = db_manager
        self.islem_turu = islem_turu
        self.cariler_map = {}
        self.setWindowTitle(f"Yeni {self.islem_turu} Kaydı (Kasa / Banka)")
        self.setFixedSize(600, 400)
        self.setup_ui()
        self.load_cariler()

    def setup_ui(self):
        l = QVBoxLayout(self)

        grp = QGroupBox(f"{self.islem_turu} Detayları")
        g = QVBoxLayout(grp)

        now_str = datetime.datetime.now().strftime("%Y%m%d-%H%M")
        
        row1 = QHBoxLayout()
        row1.addWidget(QLabel("<b>İşlem / Makbuz No:</b>"))
        prefix = "TAH" if self.islem_turu == "Tahsilat" else "TED"
        self.txt_no = QLineEdit(f"{prefix}-{now_str}")
        row1.addWidget(self.txt_no)
        g.addLayout(row1)

        row2 = QHBoxLayout()
        row2.addWidget(QLabel("<b>Cari (Müşteri / Tedarikçi):</b>"))
        self.combo_cari = QComboBox()
        self.combo_cari.setEditable(True)
        row2.addWidget(self.combo_cari)
        g.addLayout(row2)

        row3 = QHBoxLayout()
        row3.addWidget(QLabel("<b>Hesap Türü:</b>"))
        self.combo_hesap = QComboBox()
        self.combo_hesap.addItems(["Banka Havale / EFT", "Nakit Kasa", "Çek / Senet"])
        row3.addWidget(self.combo_hesap)
        g.addLayout(row3)

        row4 = QHBoxLayout()
        row4.addWidget(QLabel("<b>İşlem Tutarı (₺):</b>"))
        self.spn_tutar = QDoubleSpinBox()
        self.spn_tutar.setRange(0.01, 9999999)
        self.spn_tutar.setDecimals(2)
        row4.addWidget(self.spn_tutar)
        g.addLayout(row4)

        row5 = QHBoxLayout()
        row5.addWidget(QLabel("<b>Açıklama:</b>"))
        self.txt_aciklama = QLineEdit()
        self.txt_aciklama.setPlaceholderText("Banka hav. dekont no vb...")
        row5.addWidget(self.txt_aciklama)
        g.addLayout(row5)

        l.addWidget(grp)

        btn_box = QHBoxLayout()
        btn_save = QPushButton(f"{self.islem_turu} Kaydet ve Bakiyeye İşle")
        btn_save.setStyleSheet("background-color: #27ae60; color: white; padding: 10px; font-weight: bold;")
        btn_save.clicked.connect(self.save_islem)
        btn_box.addWidget(btn_save)

        btn_vazgec = QPushButton("Vazgeç / İptal")
        btn_vazgec.setStyleSheet("background-color: #7f8c8d; color: white; padding: 10px; font-weight: bold;")
        btn_vazgec.clicked.connect(self.reject)
        btn_box.addWidget(btn_vazgec)

        l.addLayout(btn_box)

    def load_cariler(self):
        with self.db.get_connection() as conn:
            cariler = conn.execute("SELECT ID, CariKodu, Unvan FROM Cari_Hesaplar").fetchall()
            c_list = []
            for c in cariler:
                label = f"{c['CariKodu']} - {c['Unvan']}"
                self.cariler_map[label] = c['ID']
                c_list.append(label)

            self.combo_cari.addItems(c_list)
            c_comp = QCompleter(c_list, self)
            c_comp.setCaseSensitivity(Qt.CaseInsensitive)
            self.combo_cari.setCompleter(c_comp)

    def save_islem(self):
        cari_txt = self.combo_cari.currentText()
        if cari_txt not in self.cariler_map:
            QMessageBox.warning(self, "Hata", "Geçerli bir Cari seçin!")
            return

        c_id = self.cariler_map[cari_txt]
        tutar = self.spn_tutar.value()

        if tutar <= 0:
            QMessageBox.warning(self, "Hata", "Geçerli bir tutar girin!")
            return

        with self.db.get_connection() as conn:
            # 1. Finans Kaydı
            conn.execute("""
                INSERT INTO Finans_Hareket (IslemNo, IslemTuru, CariID, HesapTuru, Tutar, Aciklama)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (self.txt_no.text().strip(), self.islem_turu, c_id, self.combo_hesap.currentText(), tutar, self.txt_aciklama.text().strip()))

            # 2. Cari Bakiye Güncelleme
            if self.islem_turu == "Tahsilat":
                # Müşteri ödeme yaptı -> Borcu düşer
                conn.execute("UPDATE Cari_Hesaplar SET Bakiye = Bakiye - ? WHERE ID = ?", (tutar, c_id))
            elif self.islem_turu == "Tediye (Ödeme)":
                # Tedarikçiye ödeme yaptık -> Tedarikçi alacağı düşer (Bakiye artar)
                conn.execute("UPDATE Cari_Hesaplar SET Bakiye = Bakiye + ? WHERE ID = ?", (tutar, c_id))

        QMessageBox.information(self, "Başarılı", f"{self.islem_turu} kaydı yapıldı. Cari bakiye güncellendi.")
        self.accept()

class BankaFormu(QWidget):
    def __init__(self, db_manager: DBManager):
        super().__init__()
        self.db = db_manager
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        l = QVBoxLayout(self)
        l.setContentsMargins(10, 10, 10, 10)

        grp = QGroupBox("Kasa & Banka Finans Hareketleri")
        v = QVBoxLayout(grp)

        btn_bar = QHBoxLayout()
        btn_tah = QPushButton("🟢 + Yeni Tahsilat Girişi (Müşteriden Alınan)")
        btn_tah.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; padding: 8px 12px;")
        btn_tah.clicked.connect(self.open_tahsilat)
        btn_bar.addWidget(btn_tah)

        btn_ted = QPushButton("🔴 - Yeni Tediye Girişi (Tedarikçiye Ödenen)")
        btn_ted.setStyleSheet("background-color: #c0392b; color: white; font-weight: bold; padding: 8px 12px;")
        btn_ted.clicked.connect(self.open_tediye)
        btn_bar.addWidget(btn_ted)

        btn_bar.addStretch()
        v.addLayout(btn_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(6)
        self.table.setHorizontalHeaderLabels(["İşlem No", "İşlem Türü", "Cari Ünvanı", "Hesap Türü", "Tutar (₺)", "Tarih"])
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Interactive)
        self.table.horizontalHeader().setStretchLastSection(True)
        v.addWidget(self.table)

        l.addWidget(grp)

    def open_tahsilat(self):
        dlg = FinansIslemDialog(self, self.db, islem_turu="Tahsilat")
        if dlg.exec_() == QDialog.Accepted:
            self.load_data()

    def open_tediye(self):
        dlg = FinansIslemDialog(self, self.db, islem_turu="Tediye (Ödeme)")
        if dlg.exec_() == QDialog.Accepted:
            self.load_data()

    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                hareketler = conn.execute("""
                    SELECT h.*, c.Unvan 
                    FROM Finans_Hareket h 
                    JOIN Cari_Hesaplar c ON h.CariID = c.ID 
                    ORDER BY h.ID DESC
                """).fetchall()

                self.table.setRowCount(len(hareketler))
                for idx, h in enumerate(hareketler):
                    self.table.setItem(idx, 0, QTableWidgetItem(h['IslemNo']))
                    self.table.setItem(idx, 1, QTableWidgetItem(h['IslemTuru']))
                    self.table.setItem(idx, 2, QTableWidgetItem(h['Unvan']))
                    self.table.setItem(idx, 3, QTableWidgetItem(h['HesapTuru']))
                    self.table.setItem(idx, 4, QTableWidgetItem(f"₺ {h['Tutar']:,.2f}"))
                    self.table.setItem(idx, 5, QTableWidgetItem(str(h['Tarih'])))
        except Exception as e:
            print(f"Finans yükleme hatası: {e}")