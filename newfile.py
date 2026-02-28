import os
import math
import random
from flask import Flask, render_template_string, request, jsonify, session, redirect
import folium
from folium.plugins import HeatMap

app = Flask(__name__)
# Render'da oturum yönetimi için gizli anahtar şarttır
app.secret_key = os.environ.get("SECRET_KEY", "daks_ozel_anahtar_99")

# --- SİSTEM VERİLERİ ---
ADMIN_UID = "Loxy010"
ADMIN_PW = "157168"
pending_apps = []

# --- MATEMATİKSEL MOTOR ---
def get_distance(lat1, lon1, lat2, lon2):
    R = 6371
    dlat, dlon = math.radians(lat2-lat1), math.radians(lon2-lon1)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon/2)**2
    return R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))

def calculate_risk(b_lat, b_lon, e_lat, e_lon, mag, depth):
    dist = get_distance(b_lat, b_lon, e_lat, e_lon)
    intensity = (mag * 12) / (math.log(max(dist, 0.1) + 2) * 2.5 + depth * 0.15)
    return min(round(intensity * 8, 1), 100)

# --- ARAYÜZ TASARIMI ---
UI_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DAKS | Akıllı Karar Sistemi</title>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        body { background: #0f172a; color: white; font-family: sans-serif; }
        .hero { padding: 60px 20px; text-align: center; background: linear-gradient(rgba(15,23,42,0.8), #0f172a), url('https://images.unsplash.com/photo-1518112166137-85899e0703ba?q=80&w=1000'); background-size: cover; border-bottom: 2px solid #3b82f6; }
        .btn-daks { border-radius: 50px; padding: 12px 30px; font-weight: bold; text-decoration: none; display: inline-block; transition: 0.3s; }
        .btn-main { background: #3b82f6; color: white; border: none; }
        .btn-auth { border: 2px solid #ef4444; color: white; margin-left: 10px; }
        .module-card { background: #1e293b; border-radius: 20px; padding: 25px; border: 1px solid #334155; }
        .form-control { background: #0f172a; border: 1px solid #334155; color: white; margin-bottom: 15px; }
        #map-frame { width: 100%; height: 500px; border-radius: 15px; border: 2px solid #ef4444; background: #000; }
    </style>
</head>
<body>
    {% if page == 'home' %}
    <div class="hero">
        <h1>DEPREM SONRASI AKILLI KARAR SİSTEMİ (DAKS) HOŞGELDİNİZ</h1>
        <p class="lead">Yapay zeka destekli sismik risk analiz ve harekat platformuna hoş geldiniz.</p>
        <div class="mt-4">
            <a href="/citizen" class="btn-daks btn-main">Bina Riskini Hesapla</a>
            <a href="/login" class="btn-daks btn-auth">Yetkili Sistemi</a>
        </div>
    </div>
    {% elif page == 'citizen' %}
    <div class="container py-5">
        <a href="/" style="color: #3b82f6;">← Geri Dön</a>
        <div class="module-card mt-3">
            <h3>🏠 Bina Analiz Modülü</h3>
            <form method="POST" action="/calc">
                <div class="row">
                    <div class="col-md-6"><label>Bina Enlem</label><input type="number" step="0.00001" name="blat" class="form-control" required></div>
                    <div class="col-md-6"><label>Bina Boylam</label><input type="number" step="0.00001" name="blon" class="form-control" required></div>
                    <div class="col-md-6"><label>Deprem Enlem</label><input type="number" step="0.00001" name="elat" class="form-control" required></div>
                    <div class="col-md-6"><label>Deprem Boylam</label><input type="number" step="0.00001" name="elon" class="form-control" required></div>
                    <div class="col-md-6"><label>Büyüklük (Mw)</label><input type="number" step="0.1" name="mag" class="form-control" required></div>
                    <div class="col-md-6"><label>Derinlik (km)</label><input type="number" name="dep" class="form-control" required></div>
                </div>
                <button class="btn btn-primary w-100">HESAPLA</button>
            </form>
            {% if res %}<div class="alert alert-danger mt-3">Tahmini Yıkılma Riski: %{{ res }}</div>{% endif %}
        </div>
    </div>
    {% elif page == 'dashboard' %}
    <div class="container-fluid p-4">
        <h3>🛡️ DAKS Harekat Paneli (Admin: {{ user }})</h3>
        <div class="row mt-4">
            <div class="col-md-3">
                <div class="module-card">
                    <label>Deprem Enlem</label><input type="number" id="mlat" class="form-control" value="38.0">
                    <label>Deprem Boylam</label><input type="number" id="mlon" class="form-control" value="37.5">
                    <label>Büyüklük</label><input type="number" id="mmag" class="form-control" value="7.6">
                    <button onclick="loadMap()" class="btn btn-danger w-100">CANLI HARİTAYI GÜNCELLE</button>
                </div>
            </div>
            <div class="col-md-9">
                <iframe id="map-frame" src="/map_init"></iframe>
            </div>
        </div>
    </div>
    <script>
        function loadMap() {
            const url = `/map_gen?lat=${$('#mlat').val()}&lon=${$('#mlon').val()}&mag=${$('#mmag').val()}`;
            $('#map-frame').attr('src', url);
        }
    </script>
    {% endif %}
</body>
</html>
"""

# --- ROTALAR ---
@app.route("/")
def home(): return render_template_string(UI_TEMPLATE, page='home')

@app.route("/citizen")
def citizen(): return render_template_string(UI_TEMPLATE, page='citizen')

@app.route("/calc", methods=["POST"])
def calc():
    r = calculate_risk(float(request.form['blat']), float(request.form['blon']), float(request.form['elat']), 
                       float(request.form['elon']), float(request.form['mag']), float(request.form['dep']))
    return render_template_string(UI_TEMPLATE, page='citizen', res=r)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("uid") == ADMIN_UID and request.form.get("pw") == ADMIN_PW:
            session['u'] = ADMIN_UID
            return redirect("/dashboard")
    return render_template_string("""
    <body style="background:#0f172a; color:white; text-align:center; padding-top:100px; font-family:sans-serif;">
        <form method="POST" style="display:inline-block; background:#1e293b; padding:40px; border-radius:20px;">
            <h2>YETKİLİ GİRİŞİ</h2>
            <input name="uid" placeholder="ID" style="display:block; margin:10px auto; padding:10px;"><br>
            <input name="pw" type="password" placeholder="Şifre" style="display:block; margin:10px auto; padding:10px;"><br>
            <button style="background:#ef4444; color:white; border:none; padding:10px 20px;">GİRİŞ</button>
        </form>
    </body>
    """)

@app.route("/dashboard")
def dashboard():
    if 'u' not in session: return redirect("/login")
    return render_template_string(UI_TEMPLATE, page='dashboard', user=session['u'])

@app.route("/map_init")
def map_init():
    return folium.Map(location=[39, 35], zoom_start=6, tiles="cartodb dark_matter")._repr_html_()

@app.route("/map_gen")
def map_gen():
    lat, lon, mag = float(request.args.get('lat')), float(request.args.get('lon')), float(request.args.get('mag'))
    m = folium.Map(location=[lat, lon], zoom_start=8, tiles="cartodb dark_matter")
    h_data = [[lat + random.gauss(0, 0.3), lon + random.gauss(0, 0.3), random.random()] for _ in range(200)]
    HeatMap(h_data).add_to(m)
    folium.Marker([lat, lon], icon=folium.Icon(color='red')).add_to(m)
    return m._repr_html_()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
                       
