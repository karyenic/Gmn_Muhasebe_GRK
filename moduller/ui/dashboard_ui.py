from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, QTableWidget, QTableWidgetItem, QHeaderView
from PyQt5.QtGui import QFont
class DashboardWindow(QWidget):
    def __init__(self, db_manager): super().__init__(); self.db = db_manager; self.setup_ui(); self.load_data()
    def setup_ui(self):
        l = QVBoxLayout(self); cards = QHBoxLayout()
        self.c_cari = self._mk("Müşteri / Cari", "#2980b9")
        self.c_stok = self._mk("Toplam Ürün", "#27ae60")
        self.c_sip = self._mk("Açık Siparişler", "#f39c12")
        self.c_kas = self._mk("Kasa Bakiyesi", "#8e44ad")
        cards.addWidget(self.c_cari); cards.addWidget(self.c_stok); cards.addWidget(self.c_sip); cards.addWidget(self.c_kas); l.addLayout(cards)
        self.table = QTableWidget(); self.table.setColumnCount(4); self.table.setHorizontalHeaderLabels(["Tür", "Açıklama", "Tutar (₺)", "Tarih"])
        self.table.horizontalHeader().setSectionResizeMode(1, QHeaderView.Stretch); l.addWidget(self.table)
    def _mk(self, t, c):
        f = QFrame(); f.setStyleSheet(f"background-color:{c}; color:white; border-radius:8px; padding:15px;")
        v = QVBoxLayout(f); v.addWidget(QLabel(t)); l = QLabel("0"); l.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold)); v.addWidget(l); return f
    def load_data(self):
        try:
            with self.db.get_connection() as conn:
                self.c_cari.findChildren(QLabel)[1].setText(f"{conn.execute('SELECT COUNT(*) as c FROM Cari_Hesaplar').fetchone()['c']} Cari")
                self.c_stok.findChildren(QLabel)[1].setText(f"{conn.execute('SELECT COUNT(*) as c FROM Urunler').fetchone()['c']} Ürün")
                acik_cnt = conn.execute("SELECT COUNT(*) as c FROM Siparisler WHERE Durum!='Tamamlandı'").fetchone()['c']
                self.c_sip.findChildren(QLabel)[1].setText(f"{acik_cnt} Açık")
                tot = conn.execute("SELECT SUM(CASE WHEN IslemTuru='Tahsilat' THEN Tutar ELSE -Tutar END) as t FROM Finans_Hareket").fetchone()['t'] or 0
                self.c_kas.findChildren(QLabel)[1].setText(f"₺ {tot:,.2f}")
        except Exception as e:
            print(f"Dashboard hatası: {e}")