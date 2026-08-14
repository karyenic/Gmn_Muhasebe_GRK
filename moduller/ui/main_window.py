from PyQt5.QtWidgets import QMainWindow, QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel
from moduller.ui.cari_ui import CariWindow
from moduller.ui.stok_ui import StokWindow
from moduller.ui.siparis_ui import SiparisWindow
from moduller.ui.finans_ui import FinansWindow
from moduller.ui.iade_fatura_ui import IadeFaturaWindow

class MainWindow(QMainWindow):
    def __init__(self, db_manager, firma_adi, kullanici):
        super().__init__()
        self.db_mgr = db_manager
        self.setWindowTitle(f"Muhasebe ERP - {firma_adi}")
        self.resize(850, 500)

        self.child_windows = []

        central_widget = QWidget()
        layout = QVBoxLayout()

        lbl_info = QLabel(f"Aktif Firma: {firma_adi}\nOturum Açan: {kullanici}")
        layout.addWidget(lbl_info)

        btn_layout = QHBoxLayout()

        btn_cari = QPushButton("Cari Yönetimi")
        btn_cari.clicked.connect(lambda: self.open_window(CariWindow))
        btn_layout.addWidget(btn_cari)

        btn_stok = QPushButton("Stok / Ürünler")
        btn_stok.clicked.connect(lambda: self.open_window(StokWindow))
        btn_layout.addWidget(btn_stok)

        btn_siparis = QPushButton("Sipariş Oluştur")
        btn_siparis.clicked.connect(lambda: self.open_window(SiparisWindow))
        btn_layout.addWidget(btn_siparis)

        btn_finans = QPushButton("Finans (Tahsilat/Tediye)")
        btn_finans.clicked.connect(lambda: self.open_window(FinansWindow))
        btn_layout.addWidget(btn_finans)

        btn_iade = QPushButton("Satış İade Faturası")
        btn_iade.clicked.connect(lambda: self.open_window(IadeFaturaWindow))
        btn_layout.addWidget(btn_iade)

        layout.addLayout(btn_layout)
        central_widget.setLayout(layout)
        self.setCentralWidget(central_widget)

    def open_window(self, window_class):
        win = window_class(self.db_mgr)
        win.show()
        self.child_windows.append(win)