# C:\Gmn_Muhasebe\sistemi_duzelt.py

import os

base_dir = r"C:\Gmn_Muhasebe"
ui_dir = os.path.join(base_dir, "moduller", "ui")
os.makedirs(ui_dir, exist_ok=True)

# 1. STYLES.PY (3D Tactile Buton ve Kontrast Temaları)
styles_code = '''
TACTILE_STYLE = """
QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    font-size: 10pt;
}

QTableWidget {
    gridline-color: #dcdde1;
    selection-background-color: #34495e;
    selection-color: #ffffff;
    alternate-background-color: #f8f9fa;
}

QHeaderView::section {
    background-color: #2c3e50;
    color: white;
    font-weight: bold;
    padding: 6px;
    border: 1px solid #1a252f;
}

QPushButton {
    border-radius: 5px;
    padding: 8px 16px;
    font-weight: bold;
    border: 1px solid rgba(0, 0, 0, 0.2);
    border-bottom: 3px solid rgba(0, 0, 0, 0.35);
}

QPushButton:hover {
    margin-top: -1px;
    border-bottom-width: 4px;
}

QPushButton:pressed {
    margin-top: 2px;
    border-bottom-width: 1px;
}

QPushButton[btnClass="success"] {
    background-color: #2ecc71;
    color: white;
    border-bottom-color: #27ae60;
}
QPushButton[btnClass="primary"] {
    background-color: #3498db;
    color: white;
    border-bottom-color: #2980b9;
}
QPushButton[btnClass="warning"] {
    background-color: #f39c12;
    color: white;
    border-bottom-color: #d35400;
}
QPushButton[btnClass="danger"] {
    background-color: #e74c3c;
    color: white;
    border-bottom-color: #c0392b;
}
QPushButton[btnClass="purple"] {
    background-color: #9b59b6;
    color: white;
    border-bottom-color: #8e44ad;
}
"""
'''

with open(os.path.join(ui_dir, "styles.py"), "w", encoding="utf-8") as f:
    f.write(styles_code)

# 2. MONTAJ_UI.PY (Yeni İmalat & Montaj Modülü)
montaj_code = '''# C:\\Gmn_Muhasebe\\moduller\\ui\\montaj_ui.py

import datetime
import uuid
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QHeaderView, QDialog, QMessageBox, QLabel,
    QComboBox, QAbstractItemView, QShortcut
)
from PyQt5.QtGui import QFont, QColor, QKeySequence
from PyQt5.QtCore import Qt
from moduller.services.stok_service import StokService
from moduller.ui.fatura_ui import SafeSpinBox, format_tarih_tr_saat
from moduller.ui.styles import TACTILE_STYLE

class MontajEmriDialog(QDialog):
    def __init__(self, parent, db):
        super().__init__(parent)
        self.db = db
        self.stok_service = StokService(db)
        self.setStyleSheet(TACTILE_STYLE)
        self.setWindowTitle("⚙️ Yeni İmalat / Paket Montaj Emri Düzenle [Ctrl+S: Kaydet]")
        self.resize(900, 600)
        self.setup_ui()
        self.load_paketler()

        QShortcut(QKeySequence("Ctrl+S"), self, self.save)

    def setup_ui(self):
        l = QVBoxLayout(self)

        top = QHBoxLayout()
        self.cmb_paket = QComboBox()
        self.spn_uretim_miktari = SafeSpinBox()
        self.spn_uretim_miktari.setRange(1, 99999)
        self.spn_uretim_miktari.setValue(1)
        self.spn_uretim_miktari.valueChanged.connect(self.hesapla_gereksinim)

        top.addWidget(QLabel("<b>Üretilecek Reçeteli Paket Ürün:</b>"))
        top.addWidget(self.cmb_paket, 2)
        top.addWidget(QLabel("<b>Üretim Miktarı (Adet):</b>"))
        top.addWidget(self.spn_uretim_miktari)
        l.addLayout(top)

        grp = QGroupBox("📋 Depo Stok Yeterlilik ve Sarf Parça Analizi")
        v_g = QVBoxLayout(grp)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["Alt Parça Kodu / Adı", "Reçete Birim Miktar", "Toplam Gerekli", "Depo Mevcudu", "Stok Durumu"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.horizontalHeader().setSectionResizeMode(0, QHeaderView.Stretch)
        v_g.addWidget(self.table)
        l.addWidget(grp)

        self.lbl_maliyet = QLabel("<b>Tahmini Toplam Üretim Maliyeti: ₺ 0.00</b>")
        self.lbl_maliyet.setStyleSheet("font-size: 11pt; color: #2980b9; font-weight: bold;")
        l.addWidget(self.lbl_maliyet, alignment=Qt.AlignRight)

        btn_uretim = QPushButton("🚀 Montajı Onayla ve İmalat Girişini Yap")
        btn_uretim.setProperty("btnClass", "success")
        btn_uretim.clicked.connect(self.save)
        l.addWidget(btn_uretim)

        self.cmb_paket.currentIndexChanged.connect(self.hesapla_gereksinim)

    def load_paketler(self):
        self.paketler_map = {}
        with self.db.get_connection() as conn:
            paketler = conn.execute("SELECT ID, UrunKodu, UrunAdi, Maliyet FROM Urunler WHERE IsPaket = 1 ORDER BY UrunAdi ASC").fetchall()
            for p in paketler:
                lbl = f"{p['UrunKodu']} - {p['UrunAdi']}"
                self.paketler_map[lbl] = dict(p)
                self.cmb_paket.addItem(lbl)
        if self.paketler_map:
            self.hesapla_gereksinim()

    def hesapla_gereksinim(self):
        txt = self.cmb_paket.currentText()
        if txt not in self.paketler_map: return
        
        p_data = self.paketler_map[txt]
        ana_id = p_data['ID']
        uretim_miktari = self.spn_uretim_miktari.value()

        self.stok_yeterli = True
        toplam_maliyet = 0.0

        with self.db.get_connection() as conn:
            recete = conn.execute("""
                SELECT pr.Miktar as BirimMiktar, u.ID, u.UrunKodu, u.UrunAdi, u.Miktar as DepoStok, u.Maliyet
                FROM Paket_Recete pr
                JOIN Urunler u ON pr.AltUrunID = u.ID
                WHERE pr.AnaUrunID = ?
            """, (ana_id,)).fetchall()

            self.table.setRowCount(len(recete))
            for i, r in enumerate(recete):
                birim_mikt = float(r['BirimMiktar'])
                gerekli = birim_mikt * uretim_miktari
                depo_stok = float(r['DepoStok'] or 0.0)
                birim_maliyet = float(r['Maliyet'] or 0.0)

                toplam_maliyet += birim_maliyet * gerekli

                self.table.setItem(i, 0, QTableWidgetItem(f"{r['UrunKodu']} - {r['UrunAdi']}"))
                self.table.setItem(i, 1, QTableWidgetItem(f"{birim_mikt:,.2f}"))
                self.table.setItem(i, 2, QTableWidgetItem(f"{gerekli:,.2f} Adet"))
                self.table.setItem(i, 3, QTableWidgetItem(f"{int(depo_stok):,} Adet"))

                it_st = QTableWidgetItem()
                if depo_stok >= gerekli:
                    it_st.setText("✅ Stok Yeterli")
                    it_st.setBackground(QColor("#27ae60"))
                    it_st.setForeground(QColor("white"))
                else:
                    it_st.setText("❌ YETERSİZ STOK")
                    it_st.setBackground(QColor("#c0392b"))
                    it_st.setForeground(QColor("white"))
                    self.stok_yeterli = False

                self.table.setItem(i, 4, it_st)

        self.lbl_maliyet.setText(f"<b>Tahmini Toplam Üretim Maliyeti: ₺ {toplam_maliyet:,.2f}</b>")

    def save(self):
        if not hasattr(self, 'stok_yeterli') or not self.stok_yeterli:
            return QMessageBox.critical(self, "Üretim Engellendi", "Depoda imalat için gerekli alt parçalardan bazıları yetersiz!")

        txt = self.cmb_paket.currentText()
        p_data = self.paketler_map[txt]
        ana_id = p_data['ID']
        uretim_miktari = self.spn_uretim_miktari.value()
        now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with self.db.get_connection() as conn:
            cur = conn.cursor()

            cur.execute("UPDATE Urunler SET Miktar = Miktar + ? WHERE ID = ?", (uretim_miktari, ana_id))

            unique_id = str(uuid.uuid4())[:8].upper()
            evrak_no = f"MNT-{p_data['UrunKodu']}-{unique_id}"

            cur.execute("""
                INSERT INTO Sevkiyatlar (SiparisID, EvrakTuru, SevkiyatNo, Tarih, CariID)
                VALUES (0, 'İmalat Montaj Fişi', ?, ?, 0)
            """, (evrak_no, now_str))
            sevk_id = cur.lastrowid

            recete = cur.execute("SELECT AltUrunID, Miktar FROM Paket_Recete WHERE AnaUrunID = ?", (ana_id,)).fetchall()
            for r in recete:
                alt_id = r['AltUrunID']
                sarf_miktari = float(r['Miktar']) * uretim_miktari

                cur.execute("UPDATE Urunler SET Miktar = Miktar - ? WHERE ID = ?", (sarf_miktari, alt_id))
                cur.execute("INSERT INTO Irsaliye_Detay (SevkiyatID, UrunID, Miktar, BirimFiyat) VALUES (?, ?, ?, 0)", (sevk_id, alt_id, sarf_miktari))

            conn.commit()

        QMessageBox.information(self, "İmalat Başarılı", f"{uretim_miktari} Adet '{p_data['UrunAdi']}' montajı tamamlandı, alt parçalar stoktan düşüldü.")
        self.accept()

class MontajWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setStyleSheet(TACTILE_STYLE)
        self.setup_ui()
        self.setup_shortcuts()
        self.load_data()

    def setup_shortcuts(self):
        QShortcut(QKeySequence("F2"), self, self.open_yeni_montaj)
        QShortcut(QKeySequence("F5"), self, self.load_data)

    def setup_ui(self):
        l = QVBoxLayout(self)
        grp = QGroupBox("⚙️ İmalat & Paket Montaj Yönetimi [F2: Yeni Üretim | F5: Yenile]")
        grp.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        v = QVBoxLayout(grp)

        btn_bar = QHBoxLayout()
        btn_yeni = QPushButton("➕ Yeni İmalat / Paket Montaj Emri (F2)")
        btn_yeni.setProperty("btnClass", "success")
        btn_yeni.clicked.connect(self.open_yeni_montaj)

        btn_bar.addWidget(btn_yeni)
        btn_bar.addStretch()
        v.addLayout(btn_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(5)
        self.table.setHorizontalHeaderLabels(["ID", "Montaj Evrak No", "İmalat Tarihi", "Evrak Türü", "İşlem Durumu"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch)
        v.addWidget(self.table)

        l.addWidget(grp)

    def load_data(self):
        with self.db.get_connection() as conn:
            montajlar = conn.execute("SELECT * FROM Sevkiyatlar WHERE EvrakTuru LIKE '%İmalat%' ORDER BY ID DESC").fetchall()
            self.table.setRowCount(len(montajlar))
            for i, m in enumerate(montajlar):
                self.table.setItem(i, 0, QTableWidgetItem(str(m['ID'])))
                self.table.setItem(i, 1, QTableWidgetItem(m['SevkiyatNo']))
                self.table.setItem(i, 2, QTableWidgetItem(format_tarih_tr_saat(m['Tarih'])))
                
                it_t = QTableWidgetItem(m['EvrakTuru'])
                it_t.setBackground(QColor("#8e44ad")); it_t.setForeground(QColor("white"))
                self.table.setItem(i, 3, it_t)

                it_d = QTableWidgetItem("✅ Üretim Tamamlandı")
                it_d.setForeground(QColor("#27ae60"))
                self.table.setItem(i, 4, it_d)

    def open_yeni_montaj(self):
        if MontajEmriDialog(self, self.db).exec_() == QDialog.Accepted:
            self.load_data()
'''

with open(os.path.join(ui_dir, "montaj_ui.py"), "w", encoding="utf-8") as f:
    f.write(montaj_code)

# 3. APP.PY (Ana Uygulama Entegrasyonu)
app_code = '''# C:\\Gmn_Muhasebe\\app.py

import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QTabWidget, QVBoxLayout, QWidget
from PyQt5.QtGui import QFont
from moduller.database.db_manager import DBManager
from moduller.ui.login_ui import LoginWindow
from moduller.ui.cari_ui import CariWindow
from moduller.ui.stok_ui import StokWindow
from moduller.ui.siparis_ui import SiparisWindow
from moduller.ui.fatura_ui import FaturaWindow
from moduller.ui.finans_ui import FinansWindow
from moduller.ui.montaj_ui import MontajWindow
from moduller.ui.styles import TACTILE_STYLE

class MainWindow(QMainWindow):
    def __init__(self, db_manager, firma_unvan, yil, kullanici_adi, ad_soyad, rol):
        super().__init__()
        self.db = db_manager
        self.firma_unvan = firma_unvan
        self.yil = yil
        self.kullanici_adi = kullanici_adi
        self.ad_soyad = ad_soyad
        self.rol = rol

        self.setWindowTitle(f"GMN MUHASEBE - {self.firma_unvan} ({self.yil}) | Kullanıcı: {self.ad_soyad} [{self.rol}]")
        self.resize(1300, 850)
        self.setStyleSheet(TACTILE_STYLE)
        self.setup_ui()

    def setup_ui(self):
        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        layout = QVBoxLayout(central_widget)

        self.tabs = QTabWidget()
        self.tabs.setFont(QFont("Segoe UI", 10, QFont.Weight.Bold))

        self.tabs.addTab(CariWindow(self.db), "👥 Cari Hesaplar")
        self.tabs.addTab(StokWindow(self.db), "📦 Stok Ürünler")
        self.tabs.addTab(MontajWindow(self.db), "⚙️ İmalat & Montaj")
        self.tabs.addTab(SiparisWindow(self.db), "🛒 Sipariş Sevkiyat")
        self.tabs.addTab(FaturaWindow(self.db), "📄 Fatura İrsaliye")
        self.tabs.addTab(FinansWindow(self.db), "💰 Finans Kasa")

        layout.addWidget(self.tabs)

def main():
    app = QApplication(sys.argv)
    db = DBManager()

    def start_app(db_path, firma_unvan, yil, k_adi, ad, rol):
        db.set_active_db(db_path)
        main_win = MainWindow(db, firma_unvan, yil, k_adi, ad, rol)
        main_win.show()
        app.main_window = main_win

    login = LoginWindow(db, start_app)
    login.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
'''

with open(os.path.join(base_dir, "app.py"), "w", encoding="utf-8") as f:
    f.write(app_code)

print("✅ Tüm dosyalar, klasör yolları ve modül bağlantıları başarıyla otomatik düzeltildi!")