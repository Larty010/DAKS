import os
import math
import random
import requests # Canlı deprem verisi için şart
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import folium
from folium.plugins import HeatMap, Fullscreen, MousePosition

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "daks_commander_2026")

# --- SİSTEM VERİLERİ ---
ADMIN_UID = "Loxy010"
ADMIN_PW = "157168"
# Kayıtları gerçek bir veritabanı gibi simüle ediyoruz
pending_registrations = [
    {"ad": "Örnek Kullanıcı", "mail": "test@gmail.com", "is": "İtfaiye", "neden": "Saha ekiplerini yönetmek için."}
]

# --- CANLI DEPREM VERİSİ ÇEKME ---
def get_live_earthquakes():
    try:
        # Ücretsiz bir API üzerinden son depremleri alıyoruz
        response = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live")
        return response.json()['result'][:10] # Son 10 deprem
    except:
        return []

# --- RİSK HESAPLAMA MOTORU ---
def calculate_advanced_risk(b_lat, b_lon, e_lat, e_lon, mag, depth):
    R = 6371
    dlat, dlon = math.radians(e_lat-b_lat), math.radians(e_lon-b_lon)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(b_lat)) * math.cos(math.radians(e_lat)) * math.sin(dlon/2)**2
    dist = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    intensity = (mag * 15) / (math.log(max(dist, 0.5) + 2) * 2.8 + depth * 0.1)
    return min(round(intensity * 7.5, 2), 100.0)

# --- TASARIM (COMMAND CENTER UI) ---
UI_HTML = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <title>DAKS v3.0 | Harekat Merkezi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/all.min.css">
    <style>
        body { background: #020617; color: #f8fafc; font-family: 'Inter', sans-serif; }
        .sidebar { background: #0f172a; border-right: 1px solid #1e293b; height: 100vh; overflow-y: auto; padding: 20px; }
        .map-section { height: 100vh; position: relative; }
        .glass-card { background: rgba(30, 41, 59, 0.7); backdrop-filter: blur(10px); border: 1px solid #334155; border-radius: 12px; padding: 15px; margin-bottom: 15px; }
        .quake-item { cursor: pointer; transition: 0.3s; border-left: 4px solid #ef4444; }
        .quake-item:hover { background: #1e293b; transform: translateX(5px); }
        .neon-blue { color: #38bdf8; text-shadow: 0 0 10px #0ea5e9; }
        #map-frame { width: 100%; height: 100%; border: none; }
    </style>
</head>
<body>
    <div class="container-fluid">
        <div class="row">
            <div class="col-md-3 sidebar">
                <h4 class="neon-blue mb-4"><i class="fas fa-satellite"></i> DAKS v3.0</h4>
                
                <ul class="nav nav-pills flex-column mb-4">
                    <li class="nav-item"><a href="/" class="nav-link text-white"><i class="fas fa-home me-2"></i>Ana Sayfa</a></li>
                    <li class="nav-item"><a href="/admin_panel" class="nav-link text-white"><i class="fas fa-users-cog me-2"></i>Başvurular</a></li>
                </ul>

                <h6 class="text-secondary text-uppercase small fw-bold mb-3">Canlı Son Depremler</h6>
                <div id="quake-list">
                    {% for q in earthquakes %}
                    <div class="glass-card quake-item" onclick="loadMap('{{q.geojson.coordinates[1]}}', '{{q.geojson.coordinates[0]}}', '{{q.mag}}')">
                        <div class="d-flex justify-content-between">
                            <strong>{{ q.title.split('(')[0] }}</strong>
                            <span class="badge bg-danger">{{ q.mag }}</span>
                        </div>
                        <small class="text-secondary">{{ q.date }}</small>
                    </div>
                    {% endfor %}
                </div>
            </div>

            <div class="col-md-9 map-section p-0">
                <iframe id="map-frame" src="/map_init"></iframe>
            </div>
        </div>
    </div>

    <script>
        function loadMap(lat, lon, mag) {
            document.getElementById('map-frame').src = `/map_gen?coords=${lat},${lon}&mag=${mag}`;
        }
    </script>
</body>
</html>
"""

# --- ROTALAR ---
@app.route("/")
def index():
    if 'user' in session:
        quakes = get_live_earthquakes()
        return render_template_string(UI_HTML, earthquakes=quakes)
    return redirect("/login")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("uid") == ADMIN_UID and request.form.get("pw") == ADMIN_PW:
            session['user'] = ADMIN_UID
            return redirect("/")
    return render_template_string("""
        <body style="background:#020617; color:white; display:flex; justify-content:center; align-items:center; height:100vh; font-family:sans-serif;">
            <form method="POST" style="background:#0f172a; padding:40px; border-radius:20px; border:1px solid #334155; width:350px;">
                <h2 style="color:#38bdf8; text-align:center;">DAKS GİRİŞ</h2>
                <input name="uid" placeholder="Admin ID" style="width:100%; padding:12px; margin:15px 0; background:#020617; border:1px solid #334155; color:white;">
                <input name="pw" type="password" placeholder="Şifre" style="width:100%; padding:12px; margin-bottom:20px; background:#020617; border:1px solid #334155; color:white;">
                <button style="width:100%; background:#38bdf8; border:none; padding:12px; font-weight:bold; border-radius:5px;">SİSTEME GİR</button>
            </form>
        </body>
    """)

@app.route("/admin_panel")
def admin_panel():
    if 'user' not in session: return redirect("/login")
    return render_template_string("""
        <body style="background:#020617; color:white; padding:50px; font-family:sans-serif;">
            <a href="/" style="color:#38bdf8; text-decoration:none;">← Panele Dön</a>
            <h2 class="my-4">Gelen Yetki Başvuruları</h2>
            <table style="width:100%; border-collapse:collapse; background:#0f172a;">
                <tr style="border-bottom:2px solid #334155;">
                    <th style="padding:15px;">Ad Soyad</th><th style="padding:15px;">E-Posta</th><th style="padding:15px;">Birim</th><th style="padding:15px;">Neden</th>
                </tr>
                {% for reg in regs %}
                <tr style="border-bottom:1px solid #1e293b;">
                    <td style="padding:15px;">{{reg.ad}}</td><td style="padding:15px;">{{reg.mail}}</td><td style="padding:15px;">{{reg.is}}</td><td style="padding:15px;">{{reg.neden}}</td>
                </tr>
                {% endfor %}
            </table>
        </body>
    """, regs=pending_registrations)

@app.route("/map_init")
def map_init():
    m = folium.Map(location=[39, 35], zoom_start=6, tiles="cartodb dark_matter")
    return m._repr_html_()

@app.route("/map_gen")
def map_gen():
    coords_str = request.args.get('coords')
    lat, lon = map(float, coords_str.split(','))
    mag = float(request.args.get('mag', 4))
    
    # Harita oluşturma (Uydu ve Dark Mode seçeneğiyle)
    m = folium.Map(location=[lat, lon], zoom_start=12)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', name='Uydu Görünümü', attr='Google').add_to(m)
    folium.TileLayer('cartodb dark_matter', name='Gece Modu').add_to(m)
    folium.LayerControl().add_to(m)
    Fullscreen().add_to(m)
    MousePosition().add_to(m)
    
    # Risk noktaları simülasyonu
    heat_data = []
    for _ in range(300):
        off_lat, off_lon = random.gauss(0, 0.05), random.gauss(0, 0.05)
        p_lat, p_lon = lat + off_lat, lon + off_lon
        heat_data.append([p_lat, p_lon, 0.8])
        
        # Kritik noktaları (yüksek riskli binalar gibi) işaretle
        if random.random() > 0.98:
            folium.CircleMarker(
                [p_lat, p_lon], radius=10, color='red', fill=True, 
                popup=f"KRİTİK BÖLGE: Koordinat ({p_lat:.4f}, {p_lon:.4f})"
            ).add_to(m)

    HeatMap(heat_data, radius=25, blur=20).add_to(m)
    folium.Marker([lat, lon], icon=folium.Icon(color='darkred', icon='exclamation-triangle', prefix='fa')).add_to(m)
    
    return m._repr_html_()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
