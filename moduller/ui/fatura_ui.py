# C:\Gmn_Muhasebe\moduller\ui\fatura_ui.py

import datetime
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QTableWidget, QTableWidgetItem,
    QPushButton, QGroupBox, QHeaderView, QDialog, QMessageBox, QTextBrowser,
    QAbstractItemView, QLabel, QLineEdit, QComboBox, QTextEdit
)
from PyQt5.QtGui import QFont, QColor
from PyQt5.QtCore import Qt
from moduller.ui.styles import SafeSpinBox, SafeDoubleSpinBox

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

class FaturaDokumDialog(QDialog):
    def __init__(self, parent, db, evrak_id, evrak_turu="Fatura"):
        super().__init__(parent)
        self.db = db
        self.evrak_id = evrak_id
        self.evrak_turu = evrak_turu
        self.setWindowTitle(f"📄 {evrak_turu} Resmi Form Dökümü")
        self.resize(1200, 800) # FERAH VE GENİŞ PENCERE
        self.setup_ui()
        self.load_html()

    def setup_ui(self):
        l = QVBoxLayout(self)
        self.viewer = QTextBrowser()
        l.addWidget(self.viewer)

        btn_yazdir = QPushButton("🖨️ Yazdır / PDF Al")
        btn_yazdir.setProperty("btnClass", "success")
        btn_yazdir.clicked.connect(lambda: QMessageBox.information(self, "Yazıcı", "Yazıcıya gönderildi."))
        l.addWidget(btn_yazdir)

    def load_html(self):
        with self.db.get_connection() as conn:
            # 1. İMALAT / MONTAJ DÖKÜMÜ
            if "İmalat" in self.evrak_turu or "Montaj" in self.evrak_turu:
                sevk = conn.execute("SELECT * FROM Sevkiyatlar WHERE ID = ? OR SevkiyatNo = ?", (self.evrak_id, str(self.evrak_id))).fetchone()
                sevk_id = sevk['ID'] if sevk else self.evrak_id
                sevk_no = sevk['SevkiyatNo'] if sevk else str(self.evrak_id)
                tarih = format_tarih_tr_saat(sevk['Tarih']) if sevk else ''

                kalemler = conn.execute("""
                    SELECT idt.*, u.UrunKodu, u.UrunAdi, u.Birim 
                    FROM Irsaliye_Detay idt 
                    JOIN Urunler u ON idt.UrunID = u.ID 
                    WHERE idt.SevkiyatID = ?
                """, (sevk_id,)).fetchall()

                html = f"""
                <html><head><style>
                    body {{ font-family: Arial, sans-serif; padding: 20px; color: #2c3e50; font-size: 11pt; }}
                    table {{ width: 100%; border-collapse: collapse; margin-top: 20px; }}
                    th, td {{ border: 1px solid #bdc3c7; padding: 10px; text-align: left; }}
                    th {{ background-color: #2c3e50; color: white; }}
                </style></head>
                <body>
                    <h2>⚙️ İMALAT / PAKET MONTAJ ÜRETİM FORMU</h2>
                    <hr>
                    <p><b>Evrak No:</b> {sevk_no} | <b>Üretim Tarihi:</b> {tarih}</p>
                    <h3>📋 Harcanan / Sarf Edilen Alt Parçalar Listesi:</h3>
                    <table>
                        <tr><th>Alt Parça Kodu</th><th>Parça / Malzeme Adı</th><th>Tüketilen Miktar</th></tr>
                """
                for k in kalemler:
                    html += f"<tr><td>{k['UrunKodu']}</td><td>{k['UrunAdi']}</td><td><b>{k['Miktar']:,.2f} {k.get('Birim', 'Adet')}</b></td></tr>"

                html += "</table></body></html>"
                self.viewer.setHtml(html)
                return

            # 2. FATURA VEYA İRSALİYE DÖKÜMÜ (GELİŞMİŞ VERİ BİRLEŞTİRME)
            fat = conn.execute("SELECT f.*, c.Unvan, c.VergiDairesi, c.VergiNo, c.Adres FROM Faturalar f JOIN Cari_Hesaplar c ON f.CariID = c.ID WHERE f.ID = ? OR f.FaturaNo = ?", (self.evrak_id, str(self.evrak_id))).fetchone()
            irs = conn.execute("SELECT s.*, COALESCE(c.Unvan, c_direct.Unvan) as Unvan, COALESCE(c.VergiDairesi, c_direct.VergiDairesi) as VergiDairesi, COALESCE(c.VergiNo, c_direct.VergiNo) as VergiNo, COALESCE(c.Adres, c_direct.Adres) as Adres FROM Sevkiyatlar s LEFT JOIN Siparisler sp ON s.SiparisID = sp.ID LEFT JOIN Cari_Hesaplar c ON sp.CariID = c.ID LEFT JOIN Cari_Hesaplar c_direct ON s.CariID = c_direct.ID WHERE s.ID = ? OR s.SevkiyatNo = ?", (self.evrak_id, str(self.evrak_id))).fetchone()

            kalemler = []
            if fat:
                evrak_no = fat['FaturaNo']
                tarih = format_tarih_tr_saat(fat['Tarih'])
                unvan = fat['Unvan']
                v_d = fat['VergiDairesi'] or '-'
                v_n = fat['VergiNo'] or '-'
                adres = fat['Adres'] or '-'
                matrah = fat['ToplamTutar'] or 0.0
                iskonto = fat['IskontoTutar'] or 0.0
                masraf = fat['Masraf'] or 0.0
                kdv = fat['KDVTutari'] or 0.0
                genel = fat['GenelToplam'] or 0.0
                b_baslik = "RESMİ SATIŞ FATURASI DÖKÜMÜ"

                # Kalemleri öncelikle Fatura_Detay'dan ara
                kalemler = conn.execute("SELECT fd.*, u.UrunKodu, u.UrunAdi FROM Fatura_Detay fd JOIN Urunler u ON fd.UrunID = u.ID WHERE fd.FaturaID = ?", (fat['ID'],)).fetchall()
                
                # Eğer Fatura_Detay boşsa, bağlı olduğu İrsaliye/Sevkiyat Detayından veya Sipariş Detayından çek
                if not kalemler and fat['IrsaliyeNo']:
                    bagli_irs = conn.execute("SELECT ID, SiparisID FROM Sevkiyatlar WHERE SevkiyatNo = ?", (fat['IrsaliyeNo'],)).fetchone()
                    if bagli_irs:
                        if bagli_irs['SiparisID'] and bagli_irs['SiparisID'] > 0:
                            kalemler = conn.execute("SELECT sd.*, sd.SevkEdilen as Miktar, u.UrunKodu, u.UrunAdi FROM Siparis_Detay sd JOIN Urunler u ON sd.UrunID=u.ID WHERE sd.SiparisID=?", (bagli_irs['SiparisID'],)).fetchall()
                        else:
                            kalemler = conn.execute("SELECT idt.*, u.UrunKodu, u.UrunAdi FROM Irsaliye_Detay idt JOIN Urunler u ON idt.UrunID=u.ID WHERE idt.SevkiyatID=?", (bagli_irs['ID'],)).fetchall()

            elif irs:
                evrak_no = irs['SevkiyatNo']
                tarih = format_tarih_tr_saat(irs['Tarih'])
                unvan = irs['Unvan'] or 'Cari Unvanı Bulunamadı'
                v_d = irs['VergiDairesi'] or '-'
                v_n = irs['VergiNo'] or '-'
                adres = irs['Adres'] or '-'
                b_baslik = "SEVK İRSALİYESİ FORM DÖKÜMÜ"

                if irs['SiparisID'] and irs['SiparisID'] > 0:
                    kalemler = conn.execute("SELECT sd.*, sd.SevkEdilen as Miktar, u.UrunKodu, u.UrunAdi FROM Siparis_Detay sd JOIN Urunler u ON sd.UrunID=u.ID WHERE sd.SiparisID=?", (irs['SiparisID'],)).fetchall()
                else:
                    kalemler = conn.execute("SELECT idt.*, u.UrunKodu, u.UrunAdi FROM Irsaliye_Detay idt JOIN Urunler u ON idt.UrunID=u.ID WHERE idt.SevkiyatID=?", (irs['ID'],)).fetchall()

                matrah = sum((k['Miktar'] or 0) * (k['BirimFiyat'] or 0) for k in kalemler)
                iskonto = 0.0
                masraf = 0.0
                kdv = matrah * 0.20
                genel = matrah + kdv
            else:
                self.viewer.setHtml("<h3>❌ Evrak Kaydı Bulunamadı!</h3>")
                return

            html = f"""
            <html><head><style>
                body {{ font-family: 'Segoe UI', Arial, sans-serif; padding: 25px; color:#2c3e50; font-size: 11pt; }}
                table {{ width: 100%; border-collapse: collapse; margin-top: 15px; }}
                th, td {{ border: 1px solid #bdc3c7; padding: 10px; text-align: left; }}
                th {{ background-color: #34495e; color: white; font-weight: bold; }}
                .summary {{ font-size: 12pt; text-align: right; margin-top: 15px; }}
            </style></head>
            <body>
                <h2 style="margin:0;">GMN OTOMATİV SAN. TİC. LTD. ŞTİ.</h2>
                <hr>
                <p><b>Belge Türü:</b> {b_baslik} | <b>Evrak No:</b> {evrak_no} | <b>Tarih:</b> {tarih}<br>
                <b>Müşteri Unvanı:</b> {unvan}<br>
                <b>Vergi D. / No:</b> {v_d} - {v_n}<br>
                <b>Adres:</b> {adres}</p>
                <table>
                    <tr><th>Ürün Kodu / Adı</th><th style="text-align:center;">Miktar</th><th style="text-align:right;">Birim Fiyat</th><th style="text-align:right;">Toplam</th></tr>
            """
            for k in kalemler:
                mikt = k['Miktar'] or 0
                fiy = k['BirimFiyat'] or 0
                tot = mikt * fiy
                html += f"<tr><td>{k['UrunKodu']} - {k['UrunAdi']}</td><td style='text-align:center;'><b>{int(mikt):,} Adet</b></td><td style='text-align:right;'>₺ {fiy:,.2f}</td><td style='text-align:right;'>₺ {tot:,.2f}</td></tr>"

            html += f"""
                </table>
                <div class="summary">
                    <p><b>Ara Toplam:</b> ₺ {matrah:,.2f}<br>
                    <b>İskonto (-):</b> ₺ {iskonto:,.2f}<br>
                    <b>KDV (%20):</b> ₺ {kdv:,.2f}<br>
                    <b style="font-size:15pt; color:#c0392b;">GENEL TOPLAM: ₺ {genel:,.2f}</b></p>
                </div>
            </body></html>
            """
            self.viewer.setHtml(html)

class FaturaWindow(QWidget):
    def __init__(self, db_manager):
        super().__init__()
        self.db = db_manager
        self.setup_ui()
        self.load_data()

    def setup_ui(self):
        l = QVBoxLayout(self)
        grp = QGroupBox("📄 Fatura ve İrsaliye Yönetimi")
        grp.setFont(QFont("Segoe UI", 11, QFont.Weight.Bold))
        v = QVBoxLayout(grp)

        btn_bar = QHBoxLayout()
        btn_dokum = QPushButton("👁️ Evrak İncele / Form Dökümü Al")
        btn_dokum.setProperty("btnClass", "primary")
        btn_dokum.clicked.connect(self.open_dokum)

        btn_bar.addWidget(btn_dokum)
        btn_bar.addStretch()
        v.addLayout(btn_bar)

        self.table = QTableWidget()
        self.table.setColumnCount(8)
        self.table.setHorizontalHeaderLabels(["ID", "Evrak Türü", "Evrak No", "Cari Firma Ünvanı", "Tarih & Saat", "KDV Tutarı", "Genel Toplam (₺)", "Durum"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.setSelectionBehavior(QAbstractItemView.SelectRows)

        header = self.table.horizontalHeader()
        for c in range(8): header.setSectionResizeMode(c, QHeaderView.Interactive)
        header.setSectionResizeMode(3, QHeaderView.Stretch)
        self.table.verticalHeader().setDefaultSectionSize(38)

        self.table.doubleClicked.connect(self.open_dokum)
        v.addWidget(self.table)
        l.addWidget(grp)

    def load_data(self):
        with self.db.get_connection() as conn:
            query = """
                SELECT f.ID, f.FaturaTipi as EvrakTuru, f.FaturaNo as EvrakNo, c.Unvan, f.Tarih, f.KDVTutari, f.GenelToplam,
                       CASE WHEN f.IrsaliyeNo IS NOT NULL AND f.IrsaliyeNo != '' THEN 'Faturalandı' ELSE 'Doğrudan Fatura' END as Durum
                FROM Faturalar f JOIN Cari_Hesaplar c ON f.CariID = c.ID
                
                UNION ALL
                
                SELECT s.ID, 'Sipariş Sevk İrsaliyesi' as EvrakTuru, s.SevkiyatNo as EvrakNo, 
                       COALESCE(c.Unvan, c_direct.Unvan, 'Müşteri') as Unvan, s.Tarih, 0.0 as KDVTutari, 0.0 as GenelToplam, 'Açık İrsaliye' as Durum
                FROM Sevkiyatlar s 
                LEFT JOIN Siparisler sp ON s.SiparisID = sp.ID 
                LEFT JOIN Cari_Hesaplar c ON sp.CariID = c.ID
                LEFT JOIN Cari_Hesaplar c_direct ON s.CariID = c_direct.ID
                
                ORDER BY Tarih DESC
            """
            evraklar = conn.execute(query).fetchall()
            self.table.setRowCount(len(evraklar))
            for i, e in enumerate(evraklar):
                self.table.setItem(i, 0, QTableWidgetItem(str(e['ID'])))
                self.table.setItem(i, 1, QTableWidgetItem(str(e['EvrakTuru'])))
                self.table.setItem(i, 2, QTableWidgetItem(str(e['EvrakNo'] or '')))
                self.table.setItem(i, 3, QTableWidgetItem(str(e['Unvan'] or '')))
                self.table.setItem(i, 4, QTableWidgetItem(format_tarih_tr_saat(e['Tarih'])))
                self.table.setItem(i, 5, QTableWidgetItem(f"₺ {e['KDVTutari'] or 0.0:,.2f}"))
                self.table.setItem(i, 6, QTableWidgetItem(f"₺ {e['GenelToplam'] or 0.0:,.2f}"))
                self.table.setItem(i, 7, QTableWidgetItem(str(e['Durum'])))

    def open_dokum(self):
        r = self.table.currentRow()
        if r < 0: return QMessageBox.warning(self, "Hata", "Lütfen bir evrak seçin!")
        e_id = int(self.table.item(r, 0).text())
        e_turu = self.table.item(r, 1).text()
        FaturaDokumDialog(self, self.db, e_id, e_turu).exec_()