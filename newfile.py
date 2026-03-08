import flet as ft
import sqlite3
import random
import time
import math
import hashlib
from datetime import datetime

# =====================================================================
# BÖLÜM 1: SİBER GÜVENLİK VE KRİPTOGRAFİ MODÜLÜ
# Ulusal güvenlik standartlarında şifreleme (SHA-256)
# =====================================================================
def encrypt_password(password):
    """
    Kullanıcı şifrelerini veritabanına açık (düz metin) olarak yazmamak için
    SHA-256 algoritması ile 64 karakterlik kırılmaz bir hash (özet) oluşturur.
    """
    return hashlib.sha256(str(password).encode('utf-8')).hexdigest()

# =====================================================================
# BÖLÜM 2: VERİTABANI VE MOTOR SİSTEMİ
# =====================================================================
class DAKSDatabase:
    def __init__(self):
        self.db_name = "daks_production_master.db"
        self.conn = sqlite3.connect(self.db_name, check_same_thread=False)
        self.cur = self.conn.cursor()
        self.init_db()

    def init_db(self):
        # Genişletilmiş ve güvenli kullanıcı tablosu
        self.cur.execute("""CREATE TABLE IF NOT EXISTS users (
            uid TEXT PRIMARY KEY, 
            pw TEXT, 
            name TEXT, 
            contact TEXT, 
            role TEXT,
            created_at TEXT
        )""")
        
        # KodAdı-Gelecek Özel Yetkili Listesi
        admins = [
            ("Loxy010", "157168"), 
            ("Bdrhnq72", "157168"), 
            ("Rubiz7256", "157168"), 
            ("Nbhr121", "157168")
        ]
        
        # Yetkilileri sisteme güvenli bir şekilde kaydetme
        for u, p in admins:
            try:
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                secure_pw = encrypt_password(p)
                self.cur.execute(
                    "INSERT INTO users (uid, pw, name, role, created_at) VALUES (?,?,?,?,?)", 
                    (u, secure_pw, f"Yetkili_{u}", "ADMIN", now)
                )
            except sqlite3.IntegrityError:
                pass # Kayıt zaten varsa atla
        self.conn.commit()

# =====================================================================
# BÖLÜM 3: ANA UYGULAMA MİMARİSİ VE YAŞAM DÖNGÜSÜ
# =====================================================================
def main(page: ft.Page):
    # --- EVRENSEL ARAYÜZ AYARLARI ---
    page.title = "DAKS | Deprem Akıllı Karar Sistemi"
    page.theme_mode = ft.ThemeMode.DARK
    page.bgcolor = "#051406" # Kurumsal Afet Yönetimi Yeşili
    page.window_width = 450
    page.window_height = 850
    page.padding = 0
    
    # Oturum Yönetimi (Session)
    engine = DAKSDatabase()
    session = {"uid": None, "role": "GUEST", "name": ""}

    def show_alert(message, color="green"):
        """Sistemin altından çıkan global bildirim aracı."""
        page.snack_bar = ft.SnackBar(
            content=ft.Text(message, color="white", weight="bold"), 
            bgcolor=color,
            elevation=10,
            duration=3500
        )
        page.snack_bar.open = True
        page.update()

    # =====================================================================
    # DEPREM ERKEN UYARI SİSTEMİ (EEW) MODÜLÜ
    # =====================================================================
    def trigger_early_warning(epicenter, magnitude, distance_km):
        """
        P-Dalgası ve S-Dalgası arasındaki hız farkını hesaplayarak 
        kullanıcıya saniye bazlı geri sayım yapan hayat kurtarıcı modül.
        """
        # P-Dalgası: ~6.0 km/s | S-Dalgası (Yıkıcı): ~3.5 km/s
        p_wave_time = distance_km / 6.0
        s_wave_time = distance_km / 3.5
        time_left = int(s_wave_time - p_wave_time)
        
        if time_left < 0:
            time_left = 0

        countdown_text = ft.Text(str(time_left), size=100, weight="w900", color="white", text_align="center")
        status_text = ft.Text("ÇÖK - KAPAN - TUTUN", size=26, weight="bold", color="white", text_align="center")

        alert_dialog = ft.AlertDialog(
            modal=True,
            title=ft.Row([
                ft.Icon(ft.icons.WARNING_AMBER_ROUNDED, color="white", size=45), 
                ft.Text("ACİL DEPREM UYARISI", color="white", weight="w900")
            ]),
            content=ft.Container(
                content=ft.Column([
                    ft.Text(f"Merkez Üssü: {epicenter}", color="white", size=20, weight="bold"),
                    ft.Text(f"Tahmini Büyüklük: {magnitude} Mw", color="#FFD54F", size=18, weight="bold"),
                    ft.Divider(color="white", thickness=2),
                    ft.Text("YIKICI DALGANIN SİZE ULAŞMASINA:", color="white", size=14, text_align="center"),
                    countdown_text,
                    ft.Text("SANİYE KALDI", color="white", size=22, weight="bold", text_align="center"),
                    ft.Container(height=15),
                    status_text,
                    ft.Container(height=15),
                    ft.ProgressBar(color="white", bgcolor="#990000", height=10)
                ], horizontal_alignment="center", tight=True),
                bgcolor="#D50000", padding=25, border_radius=15
            ),
            actions=[
                ft.ElevatedButton("SİSTEMİ KAPAT (TEST BİTİŞİ)", 
                                  on_click=lambda _: close_warning_dialog(alert_dialog), 
                                  bgcolor="black", color="white", height=50)
            ],
            actions_alignment=ft.MainAxisAlignment.CENTER
        )

        page.dialog = alert_dialog
        alert_dialog.open = True
        page.update()

        # Arka planda çalışan saniye sayacı
        def countdown_task():
            nonlocal time_left
            flash_state = True
            while time_left > 0 and alert_dialog.open:
                time.sleep(1)
                time_left -= 1
                countdown_text.value = str(time_left)
                # Kırmızı şok dalgası efekti (Renk değişimi)
                alert_dialog.content.bgcolor = "#D50000" if flash_state else "#8B0000"
                flash_state = not flash_state
                page.update()
            
            if alert_dialog.open:
                countdown_text.value = "0"
                status_text.value = "SARSINTI BAŞLADI!"
                status_text.color = "#FFD54F"
                alert_dialog.content.bgcolor = "black"
                page.update()

        page.run_task(countdown_task)

    def close_warning_dialog(dialog):
        dialog.open = False
        page.update()

    # =====================================================================
    # YAN MENÜ (NAVIGATION DRAWER) DETAYLARI
    # =====================================================================
    def build_drawer():
        return ft.NavigationDrawer(
            bgcolor="#0a290c",
            elevation=30,
            controls=[
                ft.Container(height=30),
                ft.Icon(ft.icons.MULTILINE_CHART, size=60, color="#C6FF00"),
                ft.Text("DAKS SİSTEM MENÜSÜ", weight="w900", size=18, text_align="center", color="#C6FF00", letter_spacing=2),
                ft.Divider(color="white24", thickness=2),
                ft.NavigationDrawerDestination(
                    icon=ft.icons.INFO_OUTLINE, 
                    selected_icon=ft.icons.INFO, 
                    label="Hakkımızda Modülü"
                ),
                ft.NavigationDrawerDestination(
                    icon=ft.icons.SHIELD_OUTLINED, 
                    selected_icon=ft.icons.SHIELD, 
                    label="Şifre ve Güvenlik Merkezi"
                ),
                ft.Container(expand=True), 
                ft.Container(
                    content=ft.Column([
                        ft.Divider(color="white10", thickness=2),
                        ft.Text("Türk Telekom Anadolu Lisesi", size=14, weight="bold", color="white"),
                        ft.Icon(ft.icons.SATELLITE_ALT, size=50, color="#1B5E20"),
                        ft.Text("KodAdı-Gelecek Grubu Yapımı", size=12, italic=True, color="#888888")
                    ], horizontal_alignment="center", spacing=8),
                    padding=25, 
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
                show_alert("Güvenlik ayarlarına erişmek için sistemde oturum açmalısınız.", "red")
        page.drawer.open = False
        page.update()

    # =====================================================================
    # GÖRÜNÜM: AÇILIŞ VE GİRİŞ EKRANI
    # =====================================================================
    def build_splash_and_login():
        uid_inp = ft.TextField(label="Kullanıcı ID (Örn: Loxy010)", border_color="#C6FF00", prefix_icon=ft.icons.PERSON, filled=True, fill_color="#0a290c")
        pw_inp = ft.TextField(label="Sistem Şifresi", password=True, can_reveal_password=True, border_color="#C6FF00", prefix_icon=ft.icons.LOCK, filled=True, fill_color="#0a290c")
        remember_cb = ft.Checkbox(label="Beni Hatırla (Oturumu Açık Tut)", fill_color="#1B5E20")
        loading_ring = ft.ProgressRing(visible=False, color="#C6FF00", stroke_width=5)

        def attempt_login(e):
            if not uid_inp.value or not pw_inp.value:
                show_alert("Sistem Hatası: Lütfen ID ve Şifre alanlarını boş bırakmayınız.", "red")
                return
            
            loading_ring.visible = True
            btn_login.disabled = True
            page.update()
            time.sleep(0.8) # Sunucuya bağlanma simülasyonu
            
            # GİRİŞ: GİRİLEN ŞİFREYİ ŞİFRELE VE VERİTABANIYLA KIYASLA
            secure_input_pw = encrypt_password(pw_inp.value)
            engine.cur.execute("SELECT role, name FROM users WHERE uid=? AND pw=?", (uid_inp.value, secure_input_pw))
            user = engine.cur.fetchone()
            
            loading_ring.visible = False
            btn_login.disabled = False
            
            if user:
                session["uid"], session["role"], session["name"] = uid_inp.value, user[0], user[1]
                show_alert(f"Güvenli Bağlantı Kuruldu. Hoşgeldiniz, {session['name']}!", "green")
                page.go("/dashboard")
            else:
                show_alert("Siber Güvenlik İhlali: Hatalı ID veya Şifre girdiniz.", "red")
            page.update()

        btn_login = ft.ElevatedButton("GÜVENLİ GİRİŞ YAP", on_click=attempt_login, width=350, height=60, bgcolor="#1B5E20", color="white", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))

        return ft.View("/", [
            ft.Container(
                content=ft.Column([
                    ft.Container(height=50),
                    ft.Icon(ft.icons.SECURITY, size=100, color="#C6FF00"), 
                    ft.Text("DAKS", size=80, weight="w900", letter_spacing=10, color="white"),
                    ft.Text("DEPREM AKILLI KARAR SİSTEMİ", size=15, color="#C6FF00", weight="w900", letter_spacing=2),
                    ft.Container(height=40),
                    uid_inp, 
                    pw_inp, 
                    remember_cb,
                    ft.Container(height=10),
                    loading_ring,
                    btn_login,
                    ft.Container(height=15),
                    ft.OutlinedButton("YENİ HESAP OLUŞTUR (KAYIT OL)", on_click=lambda _: page.go("/register"), width=350, height=60, border_color="#C6FF00", color="#C6FF00", style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                ], horizontal_alignment="center"), 
                padding=35
            )
        ], bgcolor="#051406")

    # =====================================================================
    # GÖRÜNÜM: VATANDAŞ KAYIT VE DOĞRULAMA
    # =====================================================================
    def build_register():
        name_inp = ft.TextField(label="Nüfus Adı ve Soyadı", prefix_icon=ft.icons.BADGE, filled=True, fill_color="#0a290c")
        contact_inp = ft.TextField(label="E-posta Adresi veya Telefon Numarası", prefix_icon=ft.icons.CONTACT_MAIL, filled=True, fill_color="#0a290c")
        code_inp = ft.TextField(label="6 Haneli Doğrulama Kodu", visible=False, text_align="center", max_length=6, border_color="#C6FF00")
        progress = ft.ProgressBar(visible=False, color="#C6FF00")
        
        def send_verification(e):
            if len(name_inp.value) < 3 or len(contact_inp.value) < 5:
                show_alert("Lütfen geçerli ve eksiksiz iletişim bilgileri giriniz.", "red")
                return
            progress.visible = True
            btn_send.disabled = True
            page.update()
            time.sleep(1.5) # SMS gönderim gecikmesi
            progress.visible = False
            code_inp.visible = True
            btn_verify.visible = True
            show_alert("Sistem Mesajı: Doğrulama kodu iletişim adresinize gönderildi (Test Kodu: 123456)", "green")
            page.update()

        def complete_registration(e):
            if code_inp.value == "123456":
                new_uid = "USR" + str(random.randint(10000, 99999))
                new_pw = str(random.randint(100000, 999999))
                now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                
                # KAYIT: ŞİFREYİ VERİTABANINA YAZMADAN ÖNCE SHA-256 İLE ŞİFRELE
                secure_new_pw = encrypt_password(new_pw)
                
                engine.cur.execute("INSERT INTO users (uid, pw, name, contact, role, created_at) VALUES (?,?,?,?,?,?)", 
                                   (new_uid, secure_new_pw, name_inp.value, contact_inp.value, "USER", now))
                engine.conn.commit()
                
                dlg = ft.AlertDialog(
                    title=ft.Row([ft.Icon(ft.icons.VERIFIED_USER, color="#C6FF00"), ft.Text("KİMLİK OLUŞTURULDU", color="#C6FF00")]), 
                    content=ft.Text(f"Sayın {name_inp.value},\n\nSisteme giriş yapabilmeniz için kimlik bilgileriniz aşağıdadır:\n\nSİSTEM ID: {new_uid}\nGEÇİCİ ŞİFRE: {new_pw}\n\n(Not: Şifreniz sistemlerimizde ulusal güvenlik standartlarında kriptolanarak saklanmaktadır. Kimse tarafından okunamaz.)")
                )
                page.dialog = dlg
                dlg.open = True
                page.go("/")
            else:
                show_alert("Güvenlik İhlali: Hatalı doğrulama kodu girildi. İşlem iptal edildi.", "red")

        btn_send = ft.ElevatedButton("KİMLİK DOĞRULAMA KODU GÖNDER", on_click=send_verification, bgcolor="#1B5E20", color="white", width=400, height=55)
        btn_verify = ft.ElevatedButton("DOĞRULA VE SİSTEME KAYIT OL", on_click=complete_registration, visible=False, bgcolor="#C6FF00", color="black", width=400, height=55)

        return ft.View("/register", [
            ft.AppBar(title=ft.Text("Vatandaş Kayıt Sistemi"), bgcolor="#1B5E20"),
            ft.Container(
                content=ft.Column([
                    ft.Text("Kişisel Veri Girişi", weight="w900", color="#C6FF00", size=18),
                    ft.Text("Lütfen bilgilerinizi eksiksiz ve doğru giriniz. Afet anında bu veriler arama-kurtarma ekipleri için hayati önem taşır.", size=12, color="white70"),
                    ft.Container(height=15),
                    name_inp, 
                    contact_inp, 
                    progress,
                    ft.Container(height=25),
                    btn_send, 
                    code_inp, 
                    btn_verify
                ]), 
                padding=30
            )
        ], bgcolor="#051406")

    # =====================================================================
    # GÖRÜNÜM: HAKKIMIZDA EKRANI
    # =====================================================================
    def build_about():
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
            ft.AppBar(title=ft.Text("Ekip ve Vizyon"), bgcolor="#1B5E20"),
            ft.Container(
                content=ft.Column([
                    ft.Text("BİZ KODADI-GELECEK GRUBUYUZ", weight="w900", size=26, color="#C6FF00", text_align="center"),
                    ft.Divider(color="white24", thickness=3),
                    ft.Container(height=15),
                    ft.Text(about_text, size=16, text_align="justify", color="white", selectable=True),
                    ft.Container(expand=True),
                    ft.Icon(ft.icons.BIOTECH, size=80, color="#1B5E20", opacity=0.6)
                ], horizontal_alignment="center"), 
                padding=35, 
                expand=True
            )
        ], bgcolor="#051406")

    # =====================================================================
    # GÖRÜNÜM: ANA KONTROL PANELİ (DASHBOARD)
    # =====================================================================
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
            ft.Container(
                content=ft.Column([
                    ft.Card(
                        content=ft.Container(
                            content=ft.Column([
                                ft.Row([ft.Icon(ft.icons.ACCOUNT_TREE, color="#C6FF00"), ft.Text("PROJE VİZYONU VE AMACI", weight="w900", color="#C6FF00", size=15)]),
                                ft.Text(purpose, size=13, text_align="justify", italic=True, color="white70")
                            ]), 
                            padding=20
                        ), 
                        color="#0a290c",
                        elevation=10
                    ),
                    ft.Container(height=25),
                    ft.Text("AKTİF SİSTEM MODÜLLERİ", weight="bold", color="white", size=16),
                    ft.Divider(color="white24", thickness=2),
                    ft.Container(height=5),
                    ft.ElevatedButton(
                        content=ft.Row([ft.Icon(ft.icons.HOME_WORK_OUTLINED, size=30), ft.Text("VATANDAŞ MODÜLÜ\n(Bina Risk Analizi)", size=14, weight="w900", text_align="center")], alignment=ft.MainAxisAlignment.CENTER),
                        on_click=lambda _: page.go("/citizen"), 
                        width=400, height=80, bgcolor="#2E7D32", color="white", 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    ),
                    ft.Container(height=15),
                    ft.ElevatedButton(
                        content=ft.Row([ft.Icon(ft.icons.ADMIN_PANEL_SETTINGS, size=30), ft.Text("YETKİLİ HAREKAT MERKEZİ\n(Kritik Yönetim)", size=14, weight="w900", text_align="center")], alignment=ft.MainAxisAlignment.CENTER),
                        on_click=lambda _: page.go("/admin_map") if session["role"] == "ADMIN" else page.go("/admin_apply"), 
                        width=400, height=80, bgcolor="#8B0000", color="white", 
                        style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10))
                    )
                ], horizontal_alignment="center"), 
                padding=25
            )
        ], bgcolor="#051406")

    # =====================================================================
    # GÖRÜNÜM: VATANDAŞ MODÜLÜ (MATEMATİKSEL RİSK HESAPLAMA)
    # =====================================================================
    def build_citizen():
        bina_yasi = ft.Dropdown(label="Bina Yönetmelik Yılı", options=[ft.dropdown.Option("1999 Öncesi (Eski Tip)"), ft.dropdown.Option("2000 - 2018 Arası (Geçiş)"), ft.dropdown.Option("2018 Sonrası (Modern)")], value="2000 - 2018 Arası (Geçiş)", border_color="#C6FF00", filled=True, fill_color="#0a290c")
        zemin_tipi = ft.Dropdown(label="Jeolojik Zemin Durumu", options=[ft.dropdown.Option("Kayalık Zemin (Sağlam)"), ft.dropdown.Option("Alüvyon Zemin (Orta Risk)"), ft.dropdown.Option("Dolgu Zemin (Yüksek Risk)")], value="Alüvyon Zemin (Orta Risk)", border_color="#C6FF00", filled=True, fill_color="#0a290c")
        kat_sayisi = ft.Dropdown(label="Bina Kat Sayısı", options=[ft.dropdown.Option("1-3 Kat (Düşük Katlı)"), ft.dropdown.Option("4-8 Kat (Orta Katlı)"), ft.dropdown.Option("9+ Kat (Yüksek Katlı)")], value="4-8 Kat (Orta Katlı)", border_color="#C6FF00", filled=True, fill_color="#0a290c")

        def hesapla_risk(mag, eq_name):
            # Bilimsel Katsayılar
            k_yapi = 1.6 if "1999" in bina_yasi.value else 1.1 if "2000" in bina_yasi.value else 0.7
            k_zemin = 0.8 if "Kayalık" in zemin_tipi.value else 1.2 if "Alüvyon" in zemin_tipi.value else 1.6
            k_kat = 0.9 if "1-3" in kat_sayisi.value else 1.1 if "4-8" in kat_sayisi.value else 1.4
            
            # Dinamik Olasılık Formülü
            ham_olasilik = (math.pow(mag, 2.2)) * 0.35 * k_yapi * k_zemin * k_kat
            risk = int(min(max(ham_olasilik, 0), 100))
            
            if mag < 3.0: 
                risk = 0

            # Matris Değerlendirmesi
            if risk < 20:
                renk, durum, icon = "green", "YIKILMA RİSKİ YOK (GÜVENLİ)", ft.icons.CHECK_CIRCLE
            elif risk < 50:
                renk, durum, icon = "yellow", "DÜŞÜK HASAR BEKLENTİSİ", ft.icons.WARNING_AMBER
            elif risk < 80:
                renk, durum, icon = "orange", "YÜKSEK HASAR / KISMİ GÖÇME RİSKİ", ft.icons.CARPENTER
            else:
                renk, durum, icon = "red", "KRİTİK! TAM GÖÇME / YIKILMA BEKLENİYOR", ft.icons.DANGEROUS

            dlg = ft.AlertDialog(
                title=ft.Row([ft.Icon(icon, color=renk, size=35), ft.Text("BİNA YIKILMA OLASILIĞI", color=renk, weight="w900")]),
                content=ft.Column([
                    ft.Text(f"Referans Deprem: {eq_name} ({mag} Mw)", weight="bold", color="white", size=16),
                    ft.Divider(color="white24", thickness=2),
                    ft.Text(f"Yapısal Çarpanlar:\nYıl: {bina_yasi.value}\nZemin: {zemin_tipi.value}\nKat: {kat_sayisi.value}", size=13, color="white70"),
                    ft.Container(height=20),
                    ft.Text("SİSTEMİN HESAPLADIĞI RİSK ORANI:", size=13, color="white", weight="bold"),
                    ft.Text(f"%{risk}", size=55, color=renk, weight="w900", text_align="center"),
                    ft.ProgressBar(value=risk/100, color=renk, bgcolor="#333333", height=12),
                    ft.Container(height=10),
                    ft.Text(durum, color=renk, weight="w900", text_align="center", size=15)
                ], tight=True)
            )
            page.dialog = dlg
            dlg.open = True
            page.update()

        # Kandilli Rasathanesi Simülasyon Verileri
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
                    leading=ft.Icon(ft.icons.WAVES, color="white54", size=30),
                    title=ft.Text(f"{loc} - {mag} Mw", weight="w900", size=14), 
                    subtitle=ft.Text(date, size=12, color="#888888"),
                    trailing=ft.Icon(ft.icons.ARROW_FORWARD_IOS, size=16, color="#C6FF00"),
                    on_click=lambda e, m=mag, n=loc: hesapla_risk(m, n)
                )
            )

        return ft.View("/citizen", [
            ft.AppBar(title=ft.Text("Vatandaş Risk Modülü"), bgcolor="#1B5E20"),
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.icons.LOCATION_ON, color="#C6FF00", size=35),
                            ft.Column([
                                ft.Text("SİSTEM KONUMUNUZ TESPİT EDİLDİ", weight="w900", color="#C6FF00", size=13), 
                                ft.Text("Otomatik Kordinat: 37.8742° K / 32.4933° D", size=12, color="white70")
                            ], spacing=2)
                        ]), 
                        bgcolor="#0a290c", padding=15, border_radius=10, border=ft.border.all(2, "#1B5E20")
                    ),
                    ft.Container(height=20),
                    ft.Text("1. AŞAMA: BİNA PROFİLİNİZ", weight="w900", color="white", size=16),
                    ft.Text("Analiz için yapınızın teknik özelliklerini seçiniz.", size=12, italic=True, color="white54"),
                    bina_yasi, zemin_tipi, kat_sayisi,
                    ft.Divider(color="white24", thickness=2),
                    ft.Text("2. AŞAMA: DEPREM SİMÜLASYONU SEÇİN", weight="w900", color="white", size=16),
                    ft.Text("Aşağıdaki geçmiş depremler bulunduğunuz konumda olsaydı, binanızın yıkılma olasılığı ne olurdu?", size=12, italic=True, color="white54"),
                    ft.Container(
                        content=ft.ListView(expand=True, controls=list_controls, spacing=8), 
                        height=280
                    )
                ]), 
                padding=25
            )
        ], bgcolor="#051406")

    # =====================================================================
    # GÖRÜNÜM: YETKİLİ BAŞVURU (YAPAY ZEKA DEĞERLENDİRMESİ)
    # =====================================================================
    def build_admin_apply():
        def eval_ai(e):
            btn_apply.disabled = True
            progress.visible = True
            page.update()
            
            time.sleep(3.0) # Yapay zeka analiz süresi
            
            progress.visible = False
            dlg = ft.AlertDialog(
                title=ft.Row([ft.Icon(ft.icons.ERROR_OUTLINE, color="orange"), ft.Text("DAKS AI Analiz Sonucu", color="orange")]), 
                content=ft.Text("Sistem analizi tamamlandı.\n\nSonuç: REDDEDİLDİ.\nNeden: Harekat Merkezine yalnızca önceden yetkilendirilmiş Devlet/AFAD personeli erişebilir. Profiliniz güvenlik standartlarını karşılamıyor.")
            )
            page.dialog = dlg
            dlg.open = True
            page.go("/dashboard")

        progress = ft.ProgressBar(visible=False, color="#C6FF00")
        btn_apply = ft.ElevatedButton("YAPAY ZEKA İLE GÜVENLİK İZNİ İSTE", on_click=eval_ai, bgcolor="#C6FF00", color="black", width=400, height=55, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))

        return ft.View("/admin_apply", [
            ft.AppBar(title=ft.Text("Yetkili Erişim Talebi"), bgcolor="#1B5E20"),
            ft.Container(
                content=ft.Column([
                    ft.Container(height=20),
                    ft.Icon(ft.icons.SECURITY_UPDATE_WARNING, size=100, color="orange"),
                    ft.Text("YETKİSİZ ERİŞİM DENEMESİ", weight="w900", size=22, color="orange"),
                    ft.Text("Harekat Merkezi verileri ulusal güvenlik kapsamında korunmaktadır. Sisteme sızma girişimleri kayıt altına alınır.", text_align="center", size=14, color="white70"),
                    ft.Container(height=30),
                    ft.TextField(label="Kurum Sicil Numaranız (Zorunlu)", border_color="orange"),
                    ft.TextField(label="Görev Türü (Örn: Arama Kurtarma Amiri)", border_color="orange"),
                    ft.Container(height=10),
                    progress, 
                    ft.Container(height=15), 
                    btn_apply
                ], horizontal_alignment="center"), 
                padding=35
            )
        ], bgcolor="#051406")

    # =====================================================================
    # GÖRÜNÜM: KRİTİK HAREKAT MERKEZİ (ISI HARİTASI VE ERKEN UYARI)
    # =====================================================================
    def build_admin_map():
        def broadcast_signal(e):
            dlg = ft.AlertDialog(
                modal=True,
                title=ft.Row([ft.Icon(ft.icons.CELL_TOWER, color="red", size=35), ft.Text("⚠️ ACİL DURUM SİNYALİ", color="red", weight="w900")]),
                content=ft.Column([
                    ft.Text("5.0+ büyüklüğünde sarsıntı tespit edildi. Telefonunuzdaki DAKS sistemi konumunuzu merkeze iletiyor.", size=14),
                    ft.Container(height=10),
                    ft.Text("ŞU AN YAŞIYOR MUSUNUZ?", weight="w900", size=20, text_align="center"),
                    ft.Container(height=15),
                    ft.ElevatedButton("HAYATTAYIM & BİNAM SAĞLAM", bgcolor="green", color="white", on_click=lambda _: close_ping(), width=320, height=60),
                    ft.Container(height=10),
                    ft.ElevatedButton("HAYATTAYIM & BİNAM YIKILDI (ENKAZ)", bgcolor="red", color="white", on_click=lambda _: close_ping(), width=320, height=60)
                ], tight=True, horizontal_alignment="center")
            )
            page.dialog = dlg
            dlg.open = True
            page.update()
        
        def close_ping():
            page.dialog.open = False
            show_alert("Sistem Mesajı: Bölgeden veriler başarıyla toplandı. Isı haritası güncellendi.", "green")
            page.update()

        return ft.View("/admin_map", [
            ft.AppBar(title=ft.Text("KRİTİK HAREKAT MERKEZİ"), bgcolor="#8B0000"),
            ft.Container(
                content=ft.Column([
                    # ERKEN UYARI (EEW) SİMÜLASYON BUTONU
                    ft.ElevatedButton(
                        content=ft.Row([ft.Icon(ft.icons.RADAR, size=25), ft.Text("SİMÜLASYON: ERKEN UYARIYI TETİKLE", weight="w900", size=14)], alignment=ft.MainAxisAlignment.CENTER),
                        on_click=lambda _: trigger_early_warning("Kahramanmaraş", 7.4, 150), 
                        bgcolor="#FF6D00", color="white", width=450, height=60, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.Container(height=10),
                    
                    # PİNG SİSTEMİ BUTONU
                    ft.ElevatedButton(
                        content=ft.Row([ft.Icon(ft.icons.WIFI_TETHERING_ERROR, size=25), ft.Text("ENKAZ TESPİTİ (PİNG) GÖNDER", weight="w900", size=14)], alignment=ft.MainAxisAlignment.CENTER),
                        on_click=broadcast_signal, 
                        bgcolor="#D50000", color="white", width=450, height=60, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=8))
                    ),
                    ft.Container(height=20),
                    
                    ft.Text("BİRLEŞTİRİLMİŞ CANLI ISI HARİTASI", weight="w900", color="#C6FF00", size=18),
                    ft.Text("Enkaz altında olduğunu bildirenler ve sinyal alınamayanlar doğrudan tek kırmızı bölge olarak işaretlenmiştir.", size=12, italic=True, color="white70"),
                    ft.Container(height=10),
                    
                    # GELİŞMİŞ ISI HARİTASI DASHBOARD'U
                    ft.Container(
                        height=350, border_radius=12, border=ft.border.all(3, "#444444"), bgcolor="#000000",
                        content=ft.Column([
                            # KIRMIZI BÖLGE (KRİTİK)
                            ft.Container(
                                bgcolor="#330000", padding=20, border_radius=ft.border_radius.only(top_left=10, top_right=10),
                                content=ft.Column([
                                    ft.Row([ft.Icon(ft.icons.LOCATION_ON, color="red", size=30), ft.Text("MÜDAHALE ÖNCELİKLİ (KIRMIZI ALAN)", color="red", weight="w900", size=15)]),
                                    ft.Text("Durum: Binası Yıkılanlar + Hiç Cevap Vermeyenler", color="white70", size=12),
                                    ft.Divider(color="red", thickness=2),
                                    ft.Row([
                                        ft.Column([ft.Text("24", size=35, weight="w900", color="red"), ft.Text("Enkaz İhbarı", size=11)]),
                                        ft.Container(width=20),
                                        ft.Column([ft.Text("87", size=35, weight="w900", color="red"), ft.Text("Cevapsız", size=11)]),
                                        ft.Container(expand=True),
                                        ft.ElevatedButton("NAVİGASYON", icon=ft.icons.MAP, bgcolor="red", color="white", height=45)
                                    ], alignment=ft.MainAxisAlignment.START)
                                ])
                            ),
                            # YEŞİL BÖLGE (GÜVENLİ)
                            ft.Container(
                                bgcolor="#003300", padding=20, border_radius=ft.border_radius.only(bottom_left=10, bottom_right=10), expand=True,
                                content=ft.Column([
                                    ft.Row([ft.Icon(ft.icons.VERIFIED, color="green", size=30), ft.Text("GÜVENLİ (YEŞİL ALAN)", color="green", weight="w900", size=15)]),
                                    ft.Text("Durum: Hayatta ve Binası Sağlam Onayı Verenler", color="white70", size=12),
                                    ft.Text("Sistem Onayı Alınan Kişi: 412", size=20, weight="w900", color="green")
                                ])
                            )
                        ], spacing=0)
                    )
                ]), 
                padding=25
            )
        ], bgcolor="#051406")

    # =====================================================================
    # GÖRÜNÜM: SİBER GÜVENLİK VE ŞİFRE MERKEZİ
    # =====================================================================
    def build_security():
        old_pw = ft.TextField(label="Mevcut Eski Şifreniz", password=True, can_reveal_password=True, prefix_icon=ft.icons.PASSWORD, border_color="#C6FF00")
        new_pw = ft.TextField(label="Yeni Güvenli Şifre", password=True, can_reveal_password=True, prefix_icon=ft.icons.LOCK_RESET, border_color="#C6FF00")
        
        def update_password(e):
            if not old_pw.value or not new_pw.value:
                show_alert("Güvenlik Hatası: Alanlar boş bırakılamaz.", "orange")
                return
                
            # Veritabanındaki şifrelenmiş eski şifreyi çekiyoruz
            engine.cur.execute("SELECT pw FROM users WHERE uid=?", (session["uid"],))
            current_secure_pw = engine.cur.fetchone()[0]
            
            # Girilen eski şifreyi şifreleyip, veritabanındakiyle karşılaştır
            if encrypt_password(old_pw.value) == current_secure_pw:
                # Eşleşirse yeni şifreyi kriptolayıp kaydet
                new_secure_pw = encrypt_password(new_pw.value)
                engine.cur.execute("UPDATE users SET pw=? WHERE uid=?", (new_secure_pw, session["uid"]))
                engine.conn.commit()
                show_alert("Şifreniz sistemde GÜVENLİ bir şekilde güncellendi.", "green")
                page.go("/dashboard")
            else: 
                show_alert("Güvenlik İhlali: Mevcut şifrenizi hatalı girdiniz!", "red")

        return ft.View("/security", [
            ft.AppBar(title=ft.Text("Güvenlik Merkezi"), bgcolor="#1B5E20"),
            ft.Container(
                content=ft.Column([
                    ft.Icon(ft.icons.SHIELD, size=80, color="#C6FF00"),
                    ft.Text("Hesap Siber Güvenliği", weight="w900", size=22, color="#C6FF00"),
                    ft.Text(f"Sistem ID Numaranız: {session['uid']}", color="white70", size=14),
                    ft.Text("Tüm şifreleriniz sunucularımızda SHA-256 algoritması ile korunmaktadır.", size=12, italic=True, color="white54", text_align="center"),
                    ft.Container(height=30),
                    old_pw, 
                    new_pw, 
                    ft.Container(height=20),
                    ft.ElevatedButton("BİLGİLERİ ŞİFRELE VE GÜNCELLE", on_click=update_password, bgcolor="#1B5E20", color="white", width=400, height=60, style=ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=10)))
                ], horizontal_alignment="center"), 
                padding=35
            )
        ], bgcolor="#051406")

    # =====================================================================
    # SİSTEM YÖNLENDİRİCİSİ (ROUTER) KONTROLÜ
    # =====================================================================
    def route_change(route):
        page.views.clear()
        r = page.route
        
        # Sayfa Geçişlerini Yönetme
        if r == "/": page.views.append(build_splash_and_login())
        elif r == "/register": page.views.append(build_register())
        elif r == "/about": page.views.append(build_about())
        elif r == "/dashboard": page.views.append(build_dashboard())
        elif r == "/citizen": page.views.append(build_citizen())
        elif r == "/admin_apply": page.views.append(build_admin_apply())
        elif r == "/admin_map": page.views.append(build_admin_map())
        elif r == "/security": page.views.append(build_security())
        
        page.update()

    # Uygulamayı İlk Rota İle Başlatma
    page.on_route_change = route_change
    page.go("/")

# =====================================================================
# DAKS MOTORUNU TETİKLEME
# =====================================================================
ft.app(target=main)
