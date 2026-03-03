import flet as ft
import sqlite3
import random
import time
import math
from datetime import datetime

# =====================================================================
# 1. VERİTABANI VE SİSTEM MOTORU (GELİŞMİŞ MİMARİ)
# =====================================================================
class DAKSDatabase:
    def __init__(self):
        self.db_name = "daks_production.db"
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.cur = self.conn.cursor()
        self.init_db()

    def init_db(self):
        # Kullanıcı veritabanı detaylandırıldı (Kayıt tarihi, son giriş vb. eklenebilir)
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, 
            pw TEXT, 
            name TEXT, 
            contact TEXT, 
            role TEXT,
            created_at TEXT
        )""")
        
        # KodAdı-Gelecek Kurucu / Özel Yetkili Listesi
        admins = [
            ("Loxy010", "157168"), 
            ("Bdrhnq72", "157168"), 
            ("Rubiz7256", "157168"), 
            ("Nbhr121", "157168")
        ]
        
        for u, p in admins:
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                self.cur.execute("INSERT INTO users (uid, pw, name, role, created_at) VALUES (?,?,?,?,?)", 
                                 (u, p, f"Yetkili_{u}", "ADMIN", now))
            except sqlite3.IntegrityError:
                pass # Kayıt zaten varsa atla
        self.conn.commit()

# =====================================================================
# 2. ANA UYGULAMA DÖNGÜSÜ
# =====================================================================
def main(page: ft.Page):
    # Sayfa ve Tema Ayarları
    page.title = "DAKS | Deprem Akıllı Karar Sistemi"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#051406" # Kurumsal Koyu Yeşil
    page.window_width = 450
    page.window_height = 850
    page.padding = 0
    page.fonts = {"RobotoSlab": "https://github.com/google/fonts/raw/main/apache/robotoslab/RobotoSlab%5Bwght%5D.ttf"}
    page.theme = ft.Theme(font_family="RobotoSlab")

    # Global Oturum (Session) Yönetimi
    engine = DAKSDatabase()
    session = {"uid": None, "role": "GUEST", "name": ""}

    # Ortak UI Araçları
    def show_alert(message, color="green"):
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white", weight="bold"), 
            bgcolor=color,
            elevation=10,
            duration=3000
        )
        page.snack_bar.open = True
        page.update()

    # =====================================================================
    # 3. YAN MENÜ (NAVIGATION DRAWER) DETAYLANDIRMASI
    # =====================================================================
    def build_drawer():
        return ft.NavigationDrawer(
            bgcolor="#0a290c",
            elevation=20,
            controls=[
                ft.Container(height=30),
                ft.Icon(ft.icons.MULTILINE_CHART, size=50, color="#C6FF00"),
                ft.Text("DAKS SİSTEM MENÜSÜ", weight="bold", size=18, text_align="center", color="#C6FF00", letter_spacing=2),
                ft.Divider(color="white24", thickness=2),
                ft.NavigationDrawerDestination(
                    icon=ft.icons.INFO_OUTLINE, 
                    selected_icon=ft.icons.INFO, 
                    label="Hakkımızda"
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.icons.SHIELD_OUTLINED, 
                    selected_icon=ft.icons.SHIELD, 
                    label="Şifre ve Güvenlik"
                ),
                ft.Container(expand=True), # Esnek boşluk
                
                # Kurum ve Ekip Bilgisi (En Alt Kısım)
                ft.Container(
                    content=ft.Column([
                        ft.Divider(color="white10"),
                        ft.Text("Türk Telekom Anadolu Lisesi", size=14, weight="bold", color="white"),
                        ft.Icon(ft.icons.SATELLITE_ALT, size=45, color="#1B5E20"), # Telekom Temsili
                        ft.Text("KodAdı-Gelecek Grubu Yapımı", size=12, italic=True, color="#888888")
                    ], horizontal_alignment="center", spacing=5),
                    padding=20, 
                    alignment=ft.alignment.bottom_center
                )
            ],
            on_change=lambda e: handle_menu_click(e)
        )

    page.drawer = build_drawer()

    def handle_menu_click(e):
        idx = e.control.selected_index
        if idx == 0:
            page.go("/about")
        elif idx == 1:
            if session["uid"]:
                page.go("/security")
            else:
                show_alert("Güvenlik ayarlarına erişmek için giriş yapmalısınız.", "red")
        page.drawer.open = False
        page.update()

    # =====================================================================
    # 4. SAYFA OLUŞTURUCU FONKSİYONLAR (MODÜLER YAPI)
    # =====================================================================

    def build_splash_and_login():
        uid_inp = ft.TextField(label="Kullanıcı ID (Örn: Loxy010)", border_color="#C6FF00", prefix_icon=ft.icons.PERSON)
        pw_inp = ft.TextField(label="Sistem Şifresi", password=True, can_reveal_password=True, border_color="#C6FF00", prefix_icon=ft.icons.LOCK)
        remember_cb = ft.Checkbox(label="Beni Hatırla (Oturumu Açık Tut)", fill_color="#1B5E20")
        loading_ring = ft.ProgressRing(visible=False, color="#C6FF00")

        def attempt_login(e):
            if not uid_inp.value or not pw_inp.value:
                show_alert("Lütfen ID ve Şifre alanlarını boş bırakmayınız.", "red")
                return
            
            # Yükleme Animasyonu Simülasyonu
            loading_ring.visible = True
            btn_login.disabled = True
            page.update()
            time.sleep(0.5) # Ağa bağlanıyormuş hissi
            
            engine.cur.execute("SELECT role, name FROM users WHERE uid=? AND pw=?", (uid_inp.value, pw_inp.value))
            user = engine.cur.fetchone()
            
            loading_ring.visible = False
            btn_login.disabled = False
            
            if user:
                session["uid"], session["role"], session["name"] = uid_inp.value, user[0], user[1]
                show_alert(f"Sisteme Hoşgeldiniz, {session['name']}!", "green")
                page.go("/dashboard")
            else:
                show_alert("Sistem Hatası: ID veya Şifre uyumsuzluğu tespit edildi.", "red")
            page.update()

        btn_login = ft.ElevatedButton("GÜVENLİ GİRİŞ YAP", on_click=attempt_login, width=350, height=55, bgcolor="#1B5E20", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))

        return ft.View("/", [
            ft.Container(
                content=ft.Column([
                    ft.Container(height=50),
                    ft.Icon(ft.icons.SHOW_CHART, size=100, color="#C6FF00"), # Logo Temsili
                    ft.Text("DAKS", size=70, weight="w900", letter_spacing=8, color="white"),
                    ft.Text("DEPREM AKILLI KARAR SİSTEMİ", size=14, color="#C6FF00", weight="bold", letter_spacing=1),
                    ft.Container(height=40),
                    uid_inp, 
                    pw_inp, 
                    remember_cb,
                    ft.Container(height=10),
                    loading_ring,
                    btn_login,
                    ft.Container(height=5),
                    ft.OutlinedButton("YENİ HESAP OLUŞTUR (KAYIT OL)", on_click=lambda _: page.go("/register"), width=350, height=55, border_color="#C6FF00", color="#C6FF00", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                ], horizontal_alignment="center"), 
                padding=30
            )
        ], bgcolor="#051406")


    def build_register():
        name_inp = ft.TextField(label="Nüfus Adı ve Soyadı", prefix_icon=ft.icons.BADGE)
        contact_inp = ft.TextField(label="E-posta Adresi veya Telefon (+90)", prefix_icon=ft.icons.CONTACT_MAIL)
        code_inp = ft.TextField(label="6 Haneli Doğrulama Kodu", visible=False, text_align="center", max_length=6)
        progress = ft.ProgressBar(visible=False, color="#C6FF00")
        
        def send_verification(e):
            if len(name_inp.value) < 3 or len(contact_inp.value) < 5:
                show_alert("Lütfen geçerli iletişim bilgileri giriniz.", "red")
                return
            progress.visible = True
            btn_send.disabled = True
            page.update()
            time.sleep(1.2) # SMS Gönderim Simülasyonu
            progress.visible = False
            code_inp.visible = True
            btn_verify.visible = True
            show_alert("Sistem Mesajı: Doğrulama kodu gönderildi (Test Kodu: 123456)", "green")
            page.update()

        def complete_registration(e):
            if code_inp.value == "123456":
                # Benzersiz ID ve Şifre Üretimi
                new_uid = "USR" + str(random.randint(10000, 99999))
                new_pw = str(random.randint(100000, 999999))
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                engine.cur.execute("INSERT INTO users (uid, pw, name, contact, role, created_at) VALUES (?,?,?,?,?,?)", 
                                   (new_uid, new_pw, name_inp.value, contact_inp.value, "USER", now))
                engine.conn.commit()
                
                dlg = ft.AlertDialog(
                    title=ft.Text("KİMLİK OLUŞTURULDU", color="#C6FF00"), 
                    content=ft.Text(f"Sayın {name_inp.value},\n\nSisteme giriş yapabilmeniz için kimlik bilgileriniz aşağıdadır:\n\nSİSTEM ID: {new_uid}\nGEÇİCİ ŞİFRE: {new_pw}\n\nLütfen bu bilgileri güvenli bir yere not ediniz.")
                )
                page.dialog = dlg
                dlg.open = True
                page.go("/")
            else:
                show_alert("Güvenlik İhlali: Hatalı doğrulama kodu girildi.", "red")

        btn_send = ft.ElevatedButton("KİMLİK DOĞRULAMA KODU GÖNDER", on_click=send_verification, bgcolor="#1B5E20", color="white", width=400, height=50)
        btn_verify = ft.ElevatedButton("DOĞRULA VE SİSTEME KAYIT OL", on_click=complete_registration, visible=False, bgcolor="#C6FF00", color="black", width=400, height=50)

        return ft.View("/register", [
            ft.AppBar(title=ft.Text("Vatandaş Kayıt Sistemi"), bgcolor="#1B5E20"),
            ft.Container(content=ft.Column([
                ft.Text("Kişisel Bilgiler", weight="bold", color="#C6FF00"),
                ft.Text("Lütfen bilgilerinizi eksiksiz ve doğru giriniz. Afet anında bu veriler hayati önem taşır.", size=12, color="white70"),
                ft.Container(height=10),
                name_inp, 
                contact_inp, 
                progress,
                ft.Container(height=20),
                btn_send, 
                code_inp, 
                btn_verify
            ]), padding=25)
        ], bgcolor="#051406")


    def build_about():
        # Tam istenilen metin bloğu
        about_text = (
            "Yazılım ve fizik alanlarında çalışmalar yürüten, gerçek dünya problemlerine "
            "çözüm üretmeyi hedefleyen bir araştırma ve geliştirme ekibiyiz. Amacımız; "
            "ülkemizde ve çevremizde karşılaştığımız sorunları bilimsel yöntemlerle analiz ederek "
            "uygulanabilir ve yenilikçi teknolojik çözümler geliştirmektir.\n\n"
            "Çalışmalarımızda teorik bilgi ile pratik uygulamayı birlikte ilerleterek, "
            "toplumsal fayda sağlayan projeler üretmeye odaklanıyoruz. Her projede gözlem, "
            "analiz, tasarım ve geliştirme süreçlerini sistemli bir şekilde yürüterek "
            "sürdürülebilir ve geliştirilebilir çözümler ortaya koymayı hedefliyoruz."
        )
        return ft.View("/about", [
            ft.AppBar(title=ft.Text("KodAdı-Gelecek"), bgcolor="#1B5E20"),
            ft.Container(content=ft.Column([
                ft.Text("BİZ KODADI-GELECEK GRUBUYUZ", weight="w900", size=24, color="#C6FF00", text_align="center"),
                ft.Divider(color="white24", thickness=2),
                ft.Container(height=10),
                ft.Text(about_text, size=15, text_align="justify", color="white", selectable=True),
                ft.Container(expand=True),
                ft.Icon(ft.icons.BIOTECH, size=60, color="#1B5E20", opacity=0.5)
            ], horizontal_alignment="center"), padding=30, expand=True)
        ], bgcolor="#051406")


    def build_dashboard():
        purpose = (
            "DAKS (Deprem Akıllı Karar Sistemi), afet yönetimini dijital bir ekosisteme dönüştüren hibrit bir teknolojidir. "
            "Projemizin temel amacı; depremin ilk kritik saniyelerinde insan hatasını devre dışı bırakarak can kurtarmaktır. "
            "Sistem, kullanıcıların bina yapı verilerini ve canlı deprem büyüklüğünü harmanlayarak bir risk skoru üretir. "
            "5.0 ve üzeri sarsıntılarda otomatik devreye giren 'Yaşıyor Musunuz?' modülü, enkaz altındaki canlarımızın "
            "konumlarını yetkili ısı haritasına anlık işler. Bu sayede ekipler, 'cevap verilmeyen' ve 'binası yıkılan' "
            "noktalara saniyeler içinde müdahale edebilir."
        )
        return ft.View("/dashboard", [
            ft.AppBar(
                leading=ft.IconButton(ft.icons.MENU, on_click=lambda _: setattr(page.drawer, 'open', True) or page.update()), 
                title=ft.Text("DAKS Ana Kontrol Paneli"), 
                bgcolor="#1B5E20"
            ),
            ft.Container(content=ft.Column([
                ft.Card(
                    content=ft.Container(
                        content=ft.Column([
                            ft.Row([ft.Icon(ft.icons.ACCOUNT_TREE, color="#C6FF00"), ft.Text("PROJE VİZYONU VE AMACI", weight="bold", color="#C6FF00")]),
                            ft.Text(purpose, size=12, text_align="justify", italic=True, color="white70")
                        ]), padding=15
                    ), color="#0a290c"
                ),
                ft.Container(height=20),
                ft.Text("SİSTEM MODÜLLERİ", weight="bold", color="white"),
                ft.Divider(color="white24"),
                ft.ElevatedButton(
                    content=ft.Row([ft.Icon(ft.icons.HOME_WORK_OUTLINED), ft.Text("VATANDAŞ MODÜLÜ (Bina Risk Analizi)", size=14, weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
                    on_click=lambda _: page.go("/citizen"), width=400, height=70, bgcolor="#2E7D32", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                ),
                ft.Container(height=10),
                ft.ElevatedButton(
                    content=ft.Row([ft.Icon(ft.icons.ADMIN_PANEL_SETTINGS), ft.Text("YETKİLİ HAREKAT MERKEZİ", size=14, weight="bold")], alignment=ft.MainAxisAlignment.CENTER),
                    on_click=lambda _: page.go("/admin_map") if session["role"] == "ADMIN" else page.go("/admin_apply"), 
                    width=400, height=70, bgcolor="#8B0000", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                )
            ], horizontal_alignment="center"), padding=20)
        ], bgcolor="#051406")


    def build_citizen():
        # Yapısal Veri Girişleri (Geliştirildi: Kat Sayısı eklendi)
        bina_yasi = ft.Dropdown(label="Bina Yönetmelik Yılı", options=[ft.dropdown.Option("1999 Öncesi (Eski Tip)"), ft.dropdown.Option("2000 - 2018 Arası (Geçiş)"), ft.dropdown.Option("2018 Sonrası (Modern)")], value="2000 - 2018 Arası (Geçiş)", border_color="#C6FF00", filled=True, fill_color="#0a290c")
        zemin_tipi = ft.Dropdown(label="Jeolojik Zemin Durumu", options=[ft.dropdown.Option("Kayalık Zemin (Sağlam)"), ft.dropdown.Option("Alüvyon Zemin (Orta Risk)"), ft.dropdown.Option("Dolgu Zemin (Yüksek Risk)")], value="Alüvyon Zemin (Orta Risk)", border_color="#C6FF00", filled=True, fill_color="#0a290c")
        kat_sayisi = ft.Dropdown(label="Bina Kat Sayısı", options=[ft.dropdown.Option("1-3 Kat (Düşük Katlı)"), ft.dropdown.Option("4-8 Kat (Orta Katlı)"), ft.dropdown.Option("9+ Kat (Yüksek Katlı)")], value="4-8 Kat (Orta Katlı)", border_color="#C6FF00", filled=True, fill_color="#0a290c")

        def hesapla_risk(mag, eq_name):
            # Bilimsel Algoritma Simülasyonu
            k_yapi = 1.6 if "1999" in bina_yasi.value else 1.1 if "2000" in bina_yasi.value else 0.7
            k_zemin = 0.8 if "Kayalık" in zemin_tipi.value else 1.2 if "Alüvyon" in zemin_tipi.value else 1.6
            k_kat = 0.9 if "1-3" in kat_sayisi.value else 1.1 if "4-8" in kat_sayisi.value else 1.4
            
            # Formül: (Mw^2.2) * Çarpanlar
            ham_olasilik = (math.pow(mag, 2.2)) * 0.35 * k_yapi * k_zemin * k_kat
            risk = int(min(max(ham_olasilik, 0), 100))
            
            # 3.0 altı depremlerde sıfır risk (Amaca tam uyum)
            if mag < 3.0: 
                risk = 0

            # Renk ve Durum Matrisi
            if risk < 20:
                renk, durum, icon = "green", "YIKILMA RİSKİ YOK (GÜVENLİ)", ft.icons.CHECK_CIRCLE
            elif risk < 50:
                renk, durum, icon = "yellow", "DÜŞÜK HASAR BEKLENTİSİ", ft.icons.WARNING_AMBER
            elif risk < 80:
                renk, durum, icon = "orange", "YÜKSEK HASAR / KISMİ GÖÇME RİSKİ", ft.icons.CARPENTER
            else:
                renk, durum, icon = "red", "KRİTİK! TAM GÖÇME / YIKILMA BEKLENİYOR", ft.icons.DANGEROUS

            # Sonuç Ekranı Detaylandırıldı
            dlg = ft.AlertDialog(
                title=ft.Row([ft.Icon(icon, color=renk), ft.Text("BİNA YIKILMA OLASILIĞI", color=renk)]),
                content=ft.Column([
                    ft.Text(f"Referans Deprem: {eq_name} ({mag} Mw)", weight="bold", color="white"),
                    ft.Divider(color="white24"),
                    ft.Text(f"Yapısal Çarpanlar:\nYıl: {bina_yasi.value}\nZemin: {zemin_tipi.value}\nKat: {kat_sayisi.value}", size=12, color="white70"),
                    ft.Container(height=15),
                    ft.Text("HESAPLANAN RİSK ORANI:", size=12, color="white"),
                    ft.Text(f"%{risk}", size=45, color=renk, weight="w900", text_align="center"),
                    ft.ProgressBar(value=risk/100, color=renk, bgcolor="#333333"),
                    ft.Text(durum, color=renk, weight="bold", text_align="center")
                ], tight=True)
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

        # Kandilli Verileri Simülasyon Listesi
        eq_list = [
            ("Kahramanmaraş (Pazarcık)", 7.7, "06 Şubat 2023 - 04:17"),
            ("İzmir (Seferihisar Açıkları)", 6.6, "30 Ekim 2020 - 14:51"),
            ("Elazığ (Sivrice)", 6.8, "24 Ocak 2020 - 20:55"),
            ("Kocaeli (Gölcük)", 7.4, "17 Ağustos 1999 - 03:02"),
            ("Malatya (Pütürge)", 5.2, "25 Ocak 2024 - 10:22"),
            ("Marmara Denizi (Mikro Deprem)", 2.1, "Bugün - 08:15 (Test)")
        ]

        list_controls = []
        for loc, mag, date in eq_list:
            list_controls.append(
                ft.ListTile(
                    leading=ft.Icon(ft.icons.WAVES, color="white54"),
                    title=ft.Text(f"{loc} - {mag} Mw", weight="bold"), 
                    subtitle=ft.Text(date, size=11, color="#888888"),
                    trailing=ft.Icon(ft.icons.ARROW_FORWARD_IOS, size=14),
                    on_click=lambda e, m=mag, n=loc: hesapla_risk(m, n)
                )
            )

        return ft.View("/citizen", [
            ft.AppBar(title=ft.Text("Bina Risk ve Olasılık Analizi"), bgcolor="#1B5E20"),
            ft.Container(content=ft.Column([
                # Otomatik Konum (Metin Olarak)
                ft.Container(
                    content=ft.Row([
 
