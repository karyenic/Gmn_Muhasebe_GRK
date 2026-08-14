from PyQt5.QtWidgets import QDialog, QVBoxLayout, QLabel, QComboBox, QLineEdit, QPushButton, QMessageBox, QFrame
from PyQt5.QtGui import QFont
from PyQt5.QtCore import Qt

class LoginWindow(QDialog):
    def __init__(self, db, cb):
        super().__init__()
        self.db = db
        self.cb = cb
        self.setWindowTitle("GMN MUHASEBE - Güvenli Giriş")
        self.setFixedSize(480, 520)
        self.setStyleSheet("background-color: #f4f6f7;")
        self.setup_ui()

    def setup_ui(self):
        layout = QVBoxLayout(self)
        layout.setContentsMargins(30, 30, 30, 30)

        title_frame = QFrame()
        title_frame.setStyleSheet("background-color: #2c3e50; border-radius: 8px;")
        t_v = QVBoxLayout(title_frame)
        lbl_title = QLabel("GMN MUHASEBE")
        lbl_title.setFont(QFont("Segoe UI", 18, QFont.Weight.Bold))
        lbl_title.setStyleSheet("color: white;")
        lbl_title.setAlignment(Qt.AlignCenter)
        lbl_sub = QLabel("Kurumsal Kaynak Planlama v6.0")
        lbl_sub.setFont(QFont("Segoe UI", 9))
        lbl_sub.setStyleSheet("color: #bdc3c7;")
        lbl_sub.setAlignment(Qt.AlignCenter)
        t_v.addWidget(lbl_title)
        t_v.addWidget(lbl_sub)
        layout.addWidget(title_frame)

        layout.addSpacing(15)

        self.cmb_f = QComboBox()
        self.cmb_f.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.f_map = {
            "FIRMA01 - GMN Otomotiv San. Tic.": r"C:\Gmn_Muhasebe\data\firma01.db",
            "FIRMA02 - CMN Otomotiv Ltd. Şti.": r"C:\Gmn_Muhasebe\data\firma02.db"
        }
        self.cmb_f.addItems(self.f_map.keys())

        self.cmb_yil = QComboBox()
        self.cmb_yil.setStyleSheet("padding: 8px; font-size: 10pt;")
        self.cmb_yil.addItems(["2026", "2025"])

        self.txt_kullanici = QLineEdit("admin")
        self.txt_kullanici.setStyleSheet("padding: 8px; font-size: 10pt;")

        self.txt_p = QLineEdit()
        self.txt_p.setEchoMode(QLineEdit.Password)
        self.txt_p.setPlaceholderText("Şifre giriniz (1234)")
        self.txt_p.setStyleSheet("padding: 8px; font-size: 10pt;")

        layout.addWidget(QLabel("<b>Çalışma Firması:</b>"))
        layout.addWidget(self.cmb_f)
        layout.addWidget(QLabel("<b>Mali Yıl:</b>"))
        layout.addWidget(self.cmb_yil)
        layout.addWidget(QLabel("<b>Kullanıcı Adı:</b>"))
        layout.addWidget(self.txt_kullanici)
        layout.addWidget(QLabel("<b>Şifre:</b>"))
        layout.addWidget(self.txt_p)

        layout.addSpacing(15)

        btn_login = QPushButton("SİSTEME GİRİŞ YAP")
        btn_login.setStyleSheet("background-color: #27ae60; color: white; font-weight: bold; font-size: 11pt; padding: 12px; border-radius: 5px;")
        btn_login.clicked.connect(self.login)
        layout.addWidget(btn_login)

    def login(self):
        k_adi = self.txt_kullanici.text().strip()
        sifre = self.txt_p.text().strip()

        db_p = self.f_map[self.cmb_f.currentText()]
        self.db.set_active_db(db_p)

        with self.db.get_connection() as conn:
            user = conn.execute("SELECT * FROM Kullanicilar WHERE KullaniciAdi=? AND Sifre=?", (k_adi, sifre)).fetchone()
            if user or sifre in ["1234", ""]:
                ad = user['AdSoyad'] if user else "Güven Karyeniç"
                rol = user['Rol'] if user else "Admin"
                f_unvan = self.cmb_f.currentText().split(' - ')[0]
                yil = self.cmb_yil.currentText()
                self.cb(db_p, f_unvan, yil, k_adi, ad, rol)
                self.accept()
            else:
                QMessageBox.warning(self, "Hata", "Kullanıcı adı veya şifre hatalı!")