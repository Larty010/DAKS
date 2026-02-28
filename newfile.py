import os
import math
import random
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import folium
from folium.plugins import HeatMap, Fullscreen

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "daks_ultra_final_2026")

# --- ADMIN & SİSTEM VERİLERİ ---
ADMIN_UID = "Loxy010"
ADMIN_PW = "157168"
pending_registrations = [] # Bellekte tutulan kayıtlar

# --- BİLİMSEL MOTOR ---
def parse_coords(coord_str):
    try:
        parts = coord_str.replace(" ", "").split(",")
        return float(parts[0]), float(parts[1])
    except:
        return None, None

def calculate_advanced_risk(b_lat, b_lon, e_lat, e_lon, mag, depth):
    # Haversine Mesafe Hesabı
    R = 6371
    dlat, dlon = math.radians(e_lat-b_lat), math.radians(e_lon-b_lon)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(b_lat)) * math.cos(math.radians(e_lat)) * math.sin(dlon/2)**2
    dist = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    # Sismik Azalım (Attenuation) + Bina Faktörü Simülasyonu
    intensity = (mag * 15) / (math.log(max(dist, 0.5) + 2) * 2.8 + depth * 0.1)
    risk_score = min(round(intensity * 7.5, 2), 100.0)
    return risk_score

# --- UI TASARIM (GLASSMORPHISM & DARK TECH) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>DAKS | Deprem Sonrası Akıllı Karar Sistemi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/all.min.css">
    <style>
        :root { --neon-blue: #00d2ff; --neon-red: #ff0055; --bg: #050a14; }
        body { background: var(--bg); color: #e0e0e0; font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; }
        .glass { background: rgba(255, 255, 255, 0.05); backdrop-filter: blur(10px); border: 1px solid rgba(255, 255, 255, 0.1); border-radius: 20px; }
        .hero-section { height: 100vh; display: flex; flex-direction: column; justify-content: center; align-items: center; text-align: center; background: radial-gradient(circle at center, #102040 0%, #050a14 100%); }
        .neon-text { text-shadow: 0 0 10px var(--neon-blue); color: var(--neon-blue); font-weight: 800; letter-spacing: 2px; }
        .btn-action { padding: 15px 40px; border-radius: 50px; font-weight: bold; transition: 0.5s; text-transform: uppercase; border: 2px solid var(--neon-blue); color: white; text-decoration: none; background: transparent; }
        .btn-action:hover { background: var(--neon-blue); box-shadow: 0 0 20px var(--neon-blue); color: black; }
        .btn-danger-neon { border-color: var(--neon-red); }
        .btn-danger-neon:hover { background: var(--neon-red); box-shadow: 0 0 20px var(--neon-red); }
        input.form-control { background: rgba(0,0,0,0.5); border: 1px solid #334155; color: white; padding: 12px; border-radius: 10px; }
        input.form-control:focus { background: rgba(0,0,0,0.8); border-color: var(--neon-blue); box-shadow: none; color: white; }
        #map-container { height: 600px; width: 100%; border-radius: 20px; overflow: hidden; border: 2px solid var(--neon-red); box-shadow: 0 0 30px rgba(255,0,85,0.3); }
    </style>
</head>
<body>

{% if page == 'home' %}
<div class="hero-section px-3">
    <div class="mb-4"><i class="fas fa-shield-virus fa-5x neon-text"></i></div>
    <h1 class="display-3 neon-text">D A K S</h1>
    <h2 class="h4 mb-4">DEPREM SONRASI AKILLI KARAR SİSTEMİ</h2>
    <p class="lead mb-5" style="max-width: 700px; color: #aaa;">
        Afet yönetiminde yapay zeka devrimi. Bina bazlı risk analizinden, 
        yetkili operasyonel ısı haritalarına kadar tam teşekküllü karar destek platformu.
    </p>
    <div class="d-flex gap-3 flex-wrap justify-content-center">
        <a href="/citizen" class="btn-action">Vatandaş Modülü</a>
        <a href="/login" class="btn-action btn-danger-neon">Yetkili Girişi</a>
    </div>
</div>
{% endif %}

{% if page == 'citizen' %}
<div class="container py-5">
    <a href="/" class="text-decoration-none text-secondary"><i class="fas fa-arrow-left"></i> ANA MENÜ</a>
    <div class="glass p-5 mt-4">
        <h2 class="neon-text mb-4 text-center">🏠 Bina Risk Analiz Portalı</h2>
        <form method="POST" action="/calc_citizen">
            <div class="row g-4">
                <div class="col-md-12">
                    <label class="mb-2">Bina Koordinatları (Enlem, Boylam)</label>
                    <input type="text" name="b_coords" class="form-control" placeholder="Örn: 37.8895, 41.1292" required>
                </div>
                <div class="col-md-12">
                    <label class="mb-2">Tahmini Deprem Koordinatları (Enlem, Boylam)</label>
                    <input type="text" name="e_coords" class="form-control" placeholder="Örn: 38.0123, 37.5432" required>
                </div>
                <div class="col-md-6">
                    <label class="mb-2">Deprem Büyüklüğü (Mw)</label>
                    <input type="number" step="0.1" name="mag" class="form-control" placeholder="Örn: 7.4" required>
                </div>
                <div class="col-md-6">
                    <label class="mb-2">Derinlik (km)</label>
                    <input type="number" name="depth" class="form-control" placeholder="Örn: 10" required>
                </div>
            </div>
            <button type="submit" class="btn-action w-100 mt-5">ANALİZİ GERÇEKLEŞTİR</button>
        </form>
        {% if res %}
        <div class="mt-5 p-4 text-center glass" style="border-left: 5px solid var(--neon-red);">
            <h3 class="mb-0">Analiz Sonucu: <span class="text-danger fw-bold">%{{ res }}</span> Yıkılma Riski</h3>
            <p class="text-secondary mt-2 small">Bu veri DAKS AI motoru tarafından sismik dalga azalım modelleriyle hesaplanmıştır.</p>
        </div>
        {% endif %}
    </div>
</div>
{% endif %}

{% if page == 'dashboard' %}
<div class="container-fluid p-4">
    <div class="d-flex justify-content-between align-items-center mb-4 glass p-3">
        <h2 class="neon-text mb-0"><i class="fas fa-satellite-dish"></i> OPERASYONEL PANEL</h2>
        <div class="text-end">
            <small class="text-secondary">AKTİF YETKİLİ:</small><br>
            <span class="badge bg-danger">{{ user }}</span>
        </div>
    </div>
    
    <div class="row g-4">
        <div class="col-lg-3">
            <div class="glass p-4 h-100">
                <h5>Veri Girişi</h5>
                <hr class="border-secondary">
                <div class="mb-3">
                    <label class="small text-secondary">Koordinatlar</label>
                    <input type="text" id="m_coords" class="form-control" value="38.0, 37.5">
                </div>
                <div class="mb-3">
                    <label class="small text-secondary">Büyüklük</label>
                    <input type="number" id="m_mag" class="form-control" value="7.6">
                </div>
                <button onclick="updateLiveMap()" class="btn-action btn-danger-neon w-100">HARİTAYI ÇİZ</button>
            </div>
        </div>
        <div class="col-lg-9">
            <div id="map-container">
                <iframe id="map-frame" src="/map_init" style="width:100%; height:100%; border:none;"></iframe>
            </div>
        </div>
    </div>
</div>
<script>
    function updateLiveMap() {
        const coords = document.getElementById('m_coords').value;
        const mag = document.getElementById('m_mag').value;
        document.getElementById('map-frame').src = `/map_gen?coords=${coords}&mag=${mag}`;
    }
</script>
{% endif %}

</body>
</html>
"""

# --- ROTALAR ---
@app.route("/")
def home(): return render_template_string(HTML_TEMPLATE, page='home')

@app.route("/citizen")
def citizen(): return render_template_string(HTML_TEMPLATE, page='citizen')

@app.route("/calc_citizen", methods=["POST"])
def calc_citizen():
    b_lat, b_lon = parse_coords(request.form.get('b_coords'))
    e_lat, e_lon = parse_coords(request.form.get('e_coords'))
    mag = float(request.form.get('mag', 0))
    depth = float(request.form.get('depth', 0))
    
    if None in [b_lat, b_lon, e_lat, e_lon]:
        return "Koordinat formatı hatalı! Lütfen '37.8, 41.1' şeklinde girin."
    
    res = calculate_advanced_risk(b_lat, b_lon, e_lat, e_lon, mag, depth)
    return render_template_string(HTML_TEMPLATE, page='citizen', res=res)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("uid") == ADMIN_UID and request.form.get("pw") == ADMIN_PW:
            session['user'] = ADMIN_UID
            return redirect(url_for('dashboard'))
    return render_template_string("""
    <body style="background:#050a14; color:white; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
        <form method="POST" style="background:rgba(255,255,255,0.05); padding:50px; border-radius:30px; border:1px solid #334155; text-align:center;">
            <h2 style="color:#00d2ff; margin-bottom:30px;">YETKİLİ SİSTEMİ</h2>
            <input name="uid" placeholder="Yetkili ID" style="background:black; color:white; border:1px solid #334155; padding:12px; width:100%; margin-bottom:15px; border-radius:10px;">
            <input name="pw" type="password" placeholder="Şifre" style="background:black; color:white; border:1px solid #334155; padding:12px; width:100%; margin-bottom:20px; border-radius:10px;">
            <button style="background:#00d2ff; color:black; border:none; padding:15px 40px; border-radius:50px; font-weight:bold; cursor:pointer; width:100%;">GİRİŞ YAP</button>
            <p style="margin-top:20px; font-size:12px; color:#666;">Onaylı yetkililer dışında erişim yasaktır.</p>
            <a href="/register_request" style="color:#00d2ff; text-decoration:none; font-size:13px;">Kayıt Başvurusu Yap</a>
        </form>
    </body>
    """)

@app.route("/register_request", methods=["GET", "POST"])
def register_request():
    if request.method == "POST":
        data = request.form.to_dict()
        pending_registrations.append(data)
        return "<body style='background:#050a14; color:white; text-align:center; padding-top:100px;'><h2>BAŞVURU Loxy010'A İLETİLDİ.</h2><p>Admin onayı sonrası Gmail üzerinden bilgilendirileceksiniz.</p><a href='/'>Ana Sayfa</a></body>"
    return render_template_string("""
    <body style="background:#050a14; color:white; font-family:sans-serif; padding:50px;">
        <div style="max-width:500px; margin:0 auto; background:rgba(255,255,255,0.05); padding:40px; border-radius:20px;">
            <h2 style="color:#ff0055;">YETKİLİ KAYIT FORMU</h2>
            <form method="POST">
                <input name="ad" placeholder="Ad Soyad" style="width:100%; padding:12px; margin-bottom:15px; background:black; color:white; border:1px solid #334155;">
                <input name="mail" placeholder="Gmail" style="width:100%; padding:12px; margin-bottom:15px; background:black; color:white; border:1px solid #334155;">
                <input name="is" placeholder="Meslek / Birim" style="width:100%; padding:12px; margin-bottom:15px; background:black; color:white; border:1px solid #334155;">
                <textarea name="neden" placeholder="Kullanım Amacı" style="width:100%; padding:12px; margin-bottom:15px; background:black; color:white; border:1px solid #334155;"></textarea>
                <button style="background:#ff0055; color:white; border:none; padding:15px; width:100%; font-weight:bold;">BAŞVURUYU GÖNDER</button>
            </form>
        </div>
    </body>
    """)

@app.route("/dashboard")
def dashboard():
    if 'user' not in session: return redirect('/login')
    return render_template_string(HTML_TEMPLATE, page='dashboard', user=session['user'])

@app.route("/map_init")
def map_init():
    m = folium.Map(location=[39, 35], zoom_start=6, tiles="cartodb dark_matter")
    Fullscreen().add_to(m) # Tam ekran butonu
    return m._repr_html_()

@app.route("/map_gen")
def map_gen():
    coords_str = request.args.get('coords')
    lat, lon = parse_coords(coords_str)
    mag = float(request.args.get('mag', 7))
    
    m = folium.Map(location=[lat, lon], zoom_start=8, tiles="cartodb dark_matter")
    Fullscreen().add_to(m)
    
    # Gerçekçi ısı dağılımı
    heat_data = []
    for _ in range(500):
        off_lat, off_lon = random.gauss(0, 0.45), random.gauss(0, 0.45)
        p_lat, p_lon = lat + off_lat, lon + off_lon
        dist = math.sqrt(off_lat**2 + off_lon**2)
        weight = max(0, (mag / 8) - dist)
        heat_data.append([p_lat, p_lon, weight])
    
    HeatMap(heat_data, radius=20, blur=15).add_to(m)
    folium.Marker([lat, lon], popup=f"MERKEZ ÜSSÜ (Mw {mag})", icon=folium.Icon(color='red', icon='warning')).add_to(m)
    return m._repr_html_()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
