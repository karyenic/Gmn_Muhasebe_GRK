from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel, QLineEdit, QComboBox, QPushButton, QMessageBox, QDoubleSpinBox

class IadeFaturaWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db_mgr = db_manager
        self.setWindowTitle("Satış İade Faturası Kes")
        self.resize(450, 350)
        self.init_ui()

    def init_ui(self):
        layout = QVBoxLayout()

        self.txt_fatura_no = QLineEdit()
        self.txt_fatura_no.setPlaceholderText("İade Fatura No (Örn: IAD2026001)")

        self.cmb_cariler = QComboBox()
        self.cmb_urunler = QComboBox()
        self.load_combo_data()

        self.spn_miktar = QDoubleSpinBox()
        self.spn_miktar.setRange(0.01, 9999.00)
        self.spn_miktar.setValue(1.00)

        self.spn_birim_fiyat = QDoubleSpinBox()
        self.spn_birim_fiyat.setRange(0.00, 999999.00)

        layout.addWidget(QLabel("Fatura Numarası:"))
        layout.addWidget(self.txt_fatura_no)
        layout.addWidget(QLabel("Cari Hesabı:"))
        layout.addWidget(self.cmb_cariler)
        layout.addWidget(QLabel("İade Alınan Ürün:"))
        layout.addWidget(self.cmb_urunler)
        layout.addWidget(QLabel("İade Miktarı:"))
        layout.addWidget(self.spn_miktar)
        layout.addWidget(QLabel("Birim Fiyat:"))
        layout.addWidget(self.spn_birim_fiyat)

        btn_iade_kes = QPushButton("İade Faturasını İşle ve Stoğu Artır")
        btn_iade_kes.clicked.connect(self.iade_faturasi_kes)
        layout.addWidget(btn_iade_kes)

        self.setLayout(layout)

    def load_combo_data(self):
        with self.db_mgr.get_connection() as conn:
            cariler = conn.execute("SELECT ID, Unvan FROM Cari_Hesaplar").fetchall()
            for c in cariler:
                self.cmb_cariler.addItem(c['Unvan'], c['ID'])

            urunler = conn.execute("SELECT ID, UrunAdi FROM Urunler").fetchall()
            for u in urunler:
                self.cmb_urunler.addItem(u['UrunAdi'], u['ID'])

    def iade_faturasi_kes(self):
        fatura_no = self.txt_fatura_no.text().strip()
        cari_id = self.cmb_cariler.currentData()
        urun_id = self.cmb_urunler.currentData()
        miktar = self.spn_miktar.value()
        birim_fiyat = self.spn_birim_fiyat.value()

        if not fatura_no or not cari_id or not urun_id:
            QMessageBox.warning(self, "Hata", "Eksik alanları doldurunuz.")
            return

        toplam_tutar = miktar * birim_fiyat
        kdv_tutari = toplam_tutar * 0.20
        genel_toplam = toplam_tutar + kdv_tutari

        with self.db_mgr.get_connection() as conn:
            cursor = conn.execute("INSERT INTO Faturalar (FaturaNo, FaturaTipi, CariID, ToplamTutar, KDVTutari, GenelToplam, Aciklama) VALUES (?, 'Satış İade', ?, ?, ?, ?, 'Müşteri Satış İadesi')",
                         (fatura_no, cari_id, toplam_tutar, kdv_tutari, genel_toplam))
            
            fatura_id = cursor.lastrowid
            conn.execute("INSERT INTO Fatura_Detay (FaturaID, UrunID, Miktar, BirimFiyat, ToplamTutar) VALUES (?, ?, ?, ?, ?)",
                         (fatura_id, urun_id, miktar, birim_fiyat, toplam_tutar))

            urun = conn.execute("SELECT Miktar FROM Urunler WHERE ID = ?", (urun_id,)).fetchone()
            eski_miktar = urun['Miktar'] if urun else 0
            yeni_miktar = eski_miktar + miktar

            conn.execute("UPDATE Urunler SET Miktar = ? WHERE ID = ?", (yeni_miktar, urun_id))
            conn.execute("INSERT INTO Stok_Log (UrunID, IslemTuru, EskiMiktar, YeniMiktar, Aciklama) VALUES (?, 'Satış İade', ?, ?, ?)",
                         (urun_id, eski_miktar, yeni_miktar, f"İade Fatura No: {fatura_no}"))

            conn.execute("UPDATE Cari_Hesaplar SET Bakiye = Bakiye - ? WHERE ID = ?", (genel_toplam, cari_id))

        QMessageBox.information(self, "Başarılı", f"{fatura_no} numaralı İade Faturası kesildi.")
        self.close()