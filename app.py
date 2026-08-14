# C:\Gmn_Muhasebe\app.py

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
from moduller.ui.ayarlar_ui import AyarlarWindow
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
        self.tabs.addTab(AyarlarWindow(self.db), "⚙️ Sistem Ayarları")

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