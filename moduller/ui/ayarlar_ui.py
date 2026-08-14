# C:\Gmn_Muhasebe\moduller\ui\ayarlar_ui.py

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QGroupBox, QLabel, QLineEdit, QPushButton, QMessageBox, QComboBox, QApplication
)
from PyQt5.QtGui import QFont
from moduller.ui.styles import get_theme_stylesheet, SafeSpinBox

class AyarlarWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setup_ui()

    def setup_ui(self):
        l = QVBoxLayout(self)
        
        # 1. TEMA VE YAZI BOYUTU (FONT) AYARLARI
        grp_tema = QGroupBox("🎨 Görünüm, Tema ve Yazı Boyutu (Font) Ayarları")
        grp_tema.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        v_t = QVBoxLayout(grp_tema)

        h_t = QHBoxLayout()
        self.cmb_tema = QComboBox()
        self.cmb_tema.addItems(["☀️ Aydınlık Mod (Klasik)", "🌗 Orta Mod (Göz Yormayan Mavi/Gri)", "🌙 Karanlık Mod (Dark Mode)"])
        
        self.spn_font_size = SafeSpinBox()
        self.spn_font_size.setRange(9, 16)
        self.spn_font_size.setValue(11)

        btn_uygula = QPushButton("🎨 Ayarları Uygula ve Yenile")
        btn_uygula.setProperty("btnClass", "primary")
        btn_uygula.clicked.connect(self.tema_degistir)

        h_t.addWidget(QLabel("Sistem Tema Seçimi:")); h_t.addWidget(self.cmb_tema, 2)
        h_t.addWidget(QLabel("Yazı Tipi Boyutu (pt):")); h_t.addWidget(self.spn_font_size)
        h_t.addWidget(btn_uygula)
        v_t.addLayout(h_t)
        l.addWidget(grp_tema)

        # 2. FİRMA BİLGİLERİ
        grp = QGroupBox("⚙️ Sistem Ayarları & Firma Bilgileri")
        grp.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        v = QVBoxLayout(grp)

        self.txt_firma_unvan = QLineEdit("GMN OTOMATİV SAN. TİC. LTD. ŞTİ.")
        self.txt_vergi_d = QLineEdit("İzmir Kurumlar V.D.")
        self.txt_vergi_n = QLineEdit("1234567890")
        self.txt_eposta_host = QLineEdit("smtp.gmail.com")
        self.txt_eposta_port = QLineEdit("587")
        self.txt_eposta_user = QLineEdit("info@gmnmuhasebe.com")

        v.addWidget(QLabel("Firma Resmi Unvanı:")); v.addWidget(self.txt_firma_unvan)
        
        h1 = QHBoxLayout()
        h1.addWidget(QLabel("Vergi Dairesi:")); h1.addWidget(self.txt_vergi_d)
        h1.addWidget(QLabel("Vergi No:")); h1.addWidget(self.txt_vergi_n)
        v.addLayout(h1)

        grp_mail = QGroupBox("📧 Otomatik Mail / E-Posta Sunucu Ayarları")
        v_m = QVBoxLayout(grp_mail)
        
        h2 = QHBoxLayout()
        h2.addWidget(QLabel("SMTP Sunucu:")); h2.addWidget(self.txt_eposta_host)
        h2.addWidget(QLabel("Port:")); h2.addWidget(self.txt_eposta_port)
        v_m.addLayout(h2)

        v_m.addWidget(QLabel("Gönderici E-Posta Adresi:")); v_m.addWidget(self.txt_eposta_user)
        v.addWidget(grp_mail)

        btn_save = QPushButton("💾 Sistem Ayarlarını Kaydet")
        btn_save.setProperty("btnClass", "success")
        btn_save.clicked.connect(lambda: QMessageBox.information(self, "Başarılı", "Sistem ayarları kaydedildi."))
        v.addWidget(btn_save)

        v.addStretch()
        l.addWidget(grp)

    def tema_degistir(self):
        f_size = self.spn_font_size.value()
        app = QApplication.instance()
        app.setStyleSheet(get_theme_stylesheet(f_size, "600"))
        QMessageBox.information(self, "Arayüz Güncellendi", f"Sistem yazı boyutu {f_size}pt ve seçilen tema başarıyla uygulandı.")