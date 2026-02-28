from flask import Flask, render_template_string, request, jsonify, session
import math
import random
import folium
from folium.plugins import HeatMap

app = Flask(__name__)
app.secret_key = "daks_ultra_secret_2024"

# --- 1. SİSTEM VERİLERİ ---
# Senin özel erişim bilgilerin
ADMIN_UID = "Loxy010"
ADMIN_PW = "157168"

# Geçici başvuru listesi (Gerçekte veritabanına gider)
pending_apps = []

# --- 2. MATEMATİKSEL MOTOR (SİSMİK RİSK) ---
def get_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def calculate_risk(b_lat, b_lon, e_lat, e_lon, mag, depth):
    dist = get_distance(b_lat, b_lon, e_lat, e_lon)
    # Bilimsel Azalım Formülü (Mesafe ve Derinlik Etkisi)
    intensity = (mag * 12) / (math.log(dist + 2) * 2.5 + depth * 0.15)
    return min(round(intensity * 8, 1), 100) # % üzerinden risk

# --- 3. TASARIM VE ARAYÜZ (CSS & HTML) ---
# Tek bir HTML içinde tüm sayfaları dinamik yöneteceğiz
UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DAKS | Deprem Sonrası Akıllı Karar Sistemi</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        :root { --blue: #3b82f6; --dark: #0f172a; --card: #1e293b; --red: #ef4444; }
        body { background: var(--dark); color: white; font-family: 'Inter', sans-serif; overflow-x: hidden; }
        
        /* Navbar & Hero */
        .hero { height: 70vh; display: flex; flex-direction: column; justify-content: center; align-items: center; 
                background: linear-gradient(to bottom, rgba(15,23,42,0.7), var(--dark)), 
                url('https://images.unsplash.com/photo-1518112166137-85899e0703ba?q=80&w=2000'); background-size: cover; text-align: center; padding: 20px; }
        
        .btn-daks { padding: 15px 35px; border-radius: 50px; font-weight: bold; transition: 0.4s; text-transform: uppercase; letter-spacing: 1px; }
        .btn-main { background: var(--blue); color: white; border: none; }
        .btn-auth { border: 2px solid var(--red); color: white; background: transparent; }
        .btn-main:hover { background: #2563eb; transform: scale(1.05); }
        .btn-auth:hover { background: var(--red); transform: scale(1.05); }

        .module-card { background: var(--card); border: 1px solid #334155; border-radius: 20px; padding: 30px; height: 100%; transition: 0.3s; }
        .form-control { background: #0f172a; border: 1px solid #334155; color: white; border-radius: 10px; padding: 12px; }
        .form-control:focus { background: #1e293b; color: white; border-color: var(--blue); box-shadow: none; }
        
        #map-container { border-radius: 20px; overflow: hidden; border: 2px solid var(--red); height: 600px; width: 100%; position: relative; background: #000; }
        iframe { width: 100%; height: 100%; border: none; }
        .loading-overlay { position: absolute; top: 0; left: 0; width: 100%; height: 100%; background: rgba(0,0,0,0.7); 
                           display: none; justify-content: center; align-items: center; z-index: 100; }
    </style>
</head>
<body>

{% if page == 'home' %}
    <div class="hero">
        <h1 class="display-2 fw-bold mb-3">DEPREM SONRASI AKILLI KARAR SİSTEMİ (DAKS)</h1>
        <p class="lead mb-5" style="max-width: 800px; color: #94a3b8;">
            Afet sonrası saniyelerin kritik olduğu anlarda, yapay zeka destekli analizlerle hayat kurtaran bir karar destek platformu.
            Hasar bölgelerini belirler, ekipleri yönlendirir ve riski minimize eder.
        </p>
        <div class="d-flex gap-3 flex-wrap justify-content-center">
            <a href="/citizen" class="btn btn-daks btn-main">Bina Riskini Hesapla</a>
            <a href="/login" class="btn btn-daks btn-auth">Yetkili Sistemi</a>
        </div>
    </div>
{% endif %}

{% if page == 'citizen' %}
    <div class="container py-5">
        <a href="/" class="text-info mb-4 d-block">← Ana Menüye Dön</a>
        <div class="row">
            <div class="col-lg-6 mx-auto">
                <div class="module-card">
                    <h2 class="mb-4 text-center">🏠 Bina Risk Analizi</h2>
                    <form method="POST" action="/calculate_citizen">
                        <div class="row g-3">
                            <div class="col-md-6"><label>Bina Enlem</label><input type="number" step="0.00001" name="blat" class="form-control" placeholder="Örn: 38.4"></div>
                            <div class="col-md-6"><label>Bina Boylam</label><input type="number" step="0.00001" name="blon" class="form-control" placeholder="Örn: 27.1"></div>
                            <div class="col-md-6"><label>Deprem Enlem</label><input type="number" step="0.00001" name="elat" class="form-control"></div>
                            <div class="col-md-6"><label>Deprem Boylam</label><input type="number" step="0.00001" name="elon" class="form-control"></div>
                            <div class="col-md-6"><label>Şiddet (Mw)</label><input type="number" step="0.1" name="mag" class="form-control"></div>
                            <div class="col-md-6"><label>Derinlik (km)</label><input type="number" name="dep" class="form-control"></div>
                        </div>
                        <button class="btn btn-primary w-100 mt-4 p-3 fw-bold">ANALİZİ BAŞLAT</button>
                    </form>
                    {% if res %}
                    <div class="mt-4 alert alert-danger text-center">
                        <h4 class="mb-0">Tahmini Hasar Riski: %{{ res }}</h4>
                    </div>
                    {% endif %}
                </div>
            </div>
        </div>
    </div>
{% endif %}

{% if page == 'login' %}
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-4">
                <div class="module-card text-center">
                    <h3 class="mb-4">YETKİLİ GİRİŞİ</h3>
                    <form method="POST" action="/auth_check">
                        <input type="text" name="uid" class="form-control mb-3" placeholder="ID">
                        <input type="password" name="pw" class="form-control mb-3" placeholder="Şifre">
                        <button class="btn btn-danger w-100">GİRİŞ YAP</button>
                    </form>
                    <hr class="my-4 border-secondary">
                    <p class="small text-secondary">Sistem yetkiniz yok mu?</p>
                    <a href="/register" class="btn btn-outline-info btn-sm">Yetki Başvurusu Yap</a>
                </div>
            </div>
        </div>
    </div>
{% endif %}

{% if page == 'register' %}
    <div class="container py-5">
        <div class="col-md-6 mx-auto">
            <div class="module-card">
                <h3 class="text-center mb-4">🛡️ Yetkili Kayıt Başvurusu</h3>
                <form method="POST" action="/reg_submit">
                    <input type="text" name="ad" class="form-control mb-3" placeholder="Ad Soyad" required>
                    <input type="email" name="mail" class="form-control mb-3" placeholder="Gmail Adresiniz" required>
                    <input type="text" name="is" class="form-control mb-3" placeholder="Mesleğiniz / Kurumunuz" required>
                    <textarea name="neden" class="form-control mb-3" placeholder="Sisteme neden erişmek istiyorsunuz?" rows="3" required></textarea>
                    <button class="btn btn-success w-100 p-3">BAŞVURUYU Loxy010'A GÖNDER</button>
                </form>
            </div>
        </div>
    </div>
{% endif %}

{% if page == 'dashboard' %}
    <div class="container-fluid py-4 px-4">
        <div class="d-flex justify-content-between align-items-center mb-4">
            <h2>🛡️ DAKS Yetkili Harekat Paneli</h2>
            <span class="badge bg-danger p-2 px-3">OTURUM: {{ session_user }}</span>
        </div>
        
        <div class="row">
            <div class="col-lg-3">
                <div class="module-card">
                    <h5>Harita Parametreleri</h5>
                    <div class="mb-3">
                        <label class="small text-secondary">Deprem Enlem</label>
                        <input type="number" id="h-lat" class="form-control" value="38.0">
                    </div>
                    <div class="mb-3">
                        <label class="small text-secondary">Deprem Boylam</label>
                        <input type="number" id="h-lon" class="form-control" value="37.5">
                    </div>
                    <div class="mb-3">
                        <label class="small text-secondary">Büyüklük (Mw)</label>
                        <input type="number" id="h-mag" class="form-control" value="7.6">
                    </div>
                    <button onclick="updateMap()" class="btn btn-danger w-100 fw-bold">CANLI HARİTAYI GÜNCELLE</button>
                    <div class="mt-4 p-3 bg-dark rounded small text-secondary">
                        <strong>Not:</strong> Harita üzerinde kırmızı bölgeler en yüksek müdahale önceliği olan alanları temsil eder.
                    </div>
                </div>
            </div>
            <div class="col-lg-9">
                <div id="map-container">
                    <div class="loading-overlay" id="loader">
                        <div class="spinner-border text-danger"></div>
                        <span class="ms-3 text-white">Yapay Zeka Haritayı Çiziyor...</span>
                    </div>
                    <iframe id="live-map" src="/get_empty_map"></iframe>
                </div>
            </div>
        </div>
    </div>

    <script>
        function updateMap() {
            const lat = $('#h-lat').val();
            const lon = $('#h-lon').val();
            const mag = $('#h-mag').val();
            
            $('#loader').css('display', 'flex');
            
            // Canlı haritayı yenilemeden çekmek için AJAX
            const mapUrl = `/generate_map?lat=${lat}&lon=${lon}&mag=${mag}`;
            $('#live-map').attr('src', mapUrl);
            
            $('#live-map').on('load', function() {
                $('#loader').hide();
            });
        }
    </script>
{% endif %}

</body>
</html>
"""

# --- 4. ROTALAR VE MANTIK ---
@app.route("/")
def home(): return render_template_string(UI_TEMPLATE, page='home')

@app.route("/citizen")
def citizen(): return render_template_string(UI_TEMPLATE, page='citizen')

@app.route("/calculate_citizen", methods=["POST"])
def calc_cit():
    r = calculate_risk(float(request.form['blat']), float(request.form['blon']), 
                       float(request.form['elat']), float(request.form['elon']), 
                       float(request.form['mag']), float(request.form['dep']))
    return render_template_string(UI_TEMPLATE, page='citizen', res=r)

@app.route("/login")
def login(): return render_template_string(UI_TEMPLATE, page='login')

@app.route("/auth_check", methods=["POST"])
def auth_check():
    if request.form['uid'] == ADMIN_UID and request.form['pw'] == ADMIN_PW:
        session['user'] = ADMIN_UID
        return redirect("/dashboard")
    return redirect("/login")

@app.route("/register")
def reg(): return render_template_string(UI_TEMPLATE, page='register')

@app.route("/reg_submit", methods=["POST"])
def reg_submit():
    pending_apps.append(request.form.to_dict())
    return "<h3>Başvurunuz Loxy010'a ulaştı. Onaylandığında Gmail üzerinden bilgilendirileceksiniz.</h3>"

@app.route("/dashboard")
def dash():
    if 'user' not in session: return redirect("/login")
    return render_template_string(UI_TEMPLATE, page='dashboard', session_user=session['user'])

# --- 5. CANLI HARİTA MOTORU ---
@app.route("/get_empty_map")
def empty_map():
    m = folium.Map(location=[39, 35], zoom_start=6, tiles="cartodb dark_matter")
    return m._repr_html_()

@app.route("/generate_map")
def generate_map():
    lat = float(request.args.get('lat'))
    lon = float(request.args.get('lon'))
    mag = float(request.args.get('mag'))
    
    m = folium.Map(location=[lat, lon], zoom_start=8, tiles="cartodb dark_matter")
    
    # Isı verisi simülasyonu (Merkezden dışa doğru gerçekçi dağılım)
    heat_data = []
    for _ in range(300):
        # Deprem merkezinden rastgele mesafelerde (normal dağılım) risk noktaları
        offset_lat = random.gauss(0, 0.4)
        offset_lon = random.gauss(0, 0.4)
        p_lat, p_lon = lat + offset_lat, lon + offset_lon
        
        # Bu nokta için risk hesabı
        risk = calculate_risk(p_lat, p_lon, lat, lon, mag, 10)
        heat_data.append([p_lat, p_lon, risk/100])

    HeatMap(heat_data, radius=25, blur=15, min_opacity=0.4).add_to(m)
    folium.Marker([lat, lon], tooltip="EPİSANTR", icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
    
    return m._repr_html_()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
