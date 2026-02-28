import os
import math
import random
import requests
from flask import Flask, render_template_string, request, jsonify, session, redirect, url_for
import folium
from folium.plugins import HeatMap, Fullscreen, MousePosition

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "daks_final_victory_2026")

# --- SİSTEM VERİLERİ ---
ADMIN_UID = "Loxy010"
ADMIN_PW = "157168"
pending_registrations = [] # Kayıt başvurularının tutulduğu liste

# --- YARDIMCI FONKSİYONLAR ---
def parse_coords(coord_str):
    try:
        parts = coord_str.replace(" ", "").split(",")
        return float(parts[0]), float(parts[1])
    except:
        return None, None

def get_live_earthquakes():
    try:
        response = requests.get("https://api.orhanaydogdu.com.tr/deprem/kandilli/live")
        return response.json()['result'][:10]
    except:
        return []

def calculate_risk(b_lat, b_lon, e_lat, e_lon, mag, depth):
    R = 6371
    dlat, dlon = math.radians(e_lat-b_lat), math.radians(e_lon-b_lon)
    a = math.sin(dlat/2)**2 + math.cos(math.radians(b_lat)) * math.cos(math.radians(e_lat)) * math.sin(dlon/2)**2
    dist = R * 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    intensity = (mag * 15) / (math.log(max(dist, 0.5) + 2) * 2.8 + depth * 0.1)
    return min(round(intensity * 7.5, 2), 100.0)

# --- TASARIM (GLOBAL STİLLER) ---
CSS = """
<style>
    :root { --neon-blue: #38bdf8; --neon-red: #f43f5e; --bg: #020617; --card: #0f172a; }
    body { background: var(--bg); color: #f1f5f9; font-family: 'Inter', sans-serif; margin: 0; }
    .glass { background: var(--card); border: 1px solid #1e293b; border-radius: 15px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
    .neon-btn { border: 2px solid var(--neon-blue); color: white; padding: 12px 30px; border-radius: 50px; text-decoration: none; font-weight: bold; transition: 0.4s; display: inline-block; background: transparent; }
    .neon-btn:hover { background: var(--neon-blue); color: black; box-shadow: 0 0 20px var(--neon-blue); }
    .neon-btn-red { border-color: var(--neon-red); }
    .neon-btn-red:hover { background: var(--neon-red); box-shadow: 0 0 20px var(--neon-red); }
    .input-custom { background: #020617; border: 1px solid #334155; color: white; padding: 12px; border-radius: 8px; width: 100%; margin-bottom: 15px; }
</style>
"""

# --- SAYFA ŞABLONLARI ---
LAYOUT = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>DAKS | Deprem Karar Sistemi</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0/all.min.css">
    """ + CSS + """
</head>
<body>
    {{ content | safe }}
</body>
</html>
"""

# --- ROTALAR ---
@app.route("/")
def home():
    content = """
    <div class="container text-center" style="padding-top: 15vh;">
        <i class="fas fa-shield-alt fa-5x mb-4" style="color: var(--neon-blue);"></i>
        <h1 class="display-3 fw-bold mb-3" style="letter-spacing: 5px;">D A K S</h1>
        <p class="lead text-secondary mb-5">Deprem Sonrası Akıllı Karar ve Analiz Platformu</p>
        <div class="d-flex justify-content-center gap-4">
            <a href="/citizen" class="neon-btn">VATANDAŞ MODÜLÜ</a>
            <a href="/login" class="neon-btn neon-btn-red">YETKİLİ GİRİŞİ</a>
        </div>
    </div>
    """
    return render_template_string(LAYOUT, content=content)

@app.route("/citizen", methods=["GET", "POST"])
def citizen():
    res = None
    if request.method == "POST":
        b_lat, b_lon = parse_coords(request.form.get("b_coords"))
        e_lat, e_lon = parse_coords(request.form.get("e_coords"))
        mag = float(request.form.get("mag", 0))
        res = calculate_risk(b_lat, b_lon, e_lat, e_lon, mag, 10)
    
    content = f"""
    <div class="container py-5">
        <a href="/" class="text-secondary text-decoration-none mb-4 d-inline-block"><i class="fas fa-arrow-left"></i> Geri Dön</a>
        <div class="row justify-content-center">
            <div class="col-md-6 glass">
                <h3 class="mb-4 text-center"><i class="fas fa-home me-2"></i>Bina Risk Analizi</h3>
                <form method="POST">
                    <label class="small text-secondary mb-1">Bina Koordinatları</label>
                    <input name="b_coords" class="input-custom" placeholder="Örn: 37.88, 41.12" required>
                    <label class="small text-secondary mb-1">Deprem Koordinatları</label>
                    <input name="e_coords" class="input-custom" placeholder="Örn: 38.01, 37.54" required>
                    <label class="small text-secondary mb-1">Tahmini Büyüklük (Mw)</label>
                    <input name="mag" type="number" step="0.1" class="input-custom" placeholder="Örn: 7.4" required>
                    <button class="neon-btn w-100 mt-3">ANALİZ ET</button>
                </form>
                {"<div class='alert alert-danger mt-4 text-center'><h4>Risk Skoru: %" + str(res) + "</h4></div>" if res else ""}
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT, content=content)

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("uid") == ADMIN_UID and request.form.get("pw") == ADMIN_PW:
            session['user'] = ADMIN_UID
            return redirect("/dashboard")
    
    content = """
    <div class="container py-5 text-center">
        <div class="row justify-content-center">
            <div class="col-md-4 glass">
                <h3 class="mb-4 text-danger">YETKİLİ GİRİŞİ</h3>
                <form method="POST">
                    <input name="uid" class="input-custom" placeholder="Kullanıcı ID">
                    <input name="pw" type="password" class="input-custom" placeholder="Şifre">
                    <button class="neon-btn neon-btn-red w-100 mb-3">GİRİŞ YAP</button>
                </form>
                <p class="small text-secondary">Sistem yetkiniz yok mu?</p>
                <a href="/register" class="text-info text-decoration-none">Şimdi Kayıt Başvurusu Yap</a>
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT, content=content)

@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        pending_registrations.append(request.form.to_dict())
        return "<body style='background:#020617;color:white;text-align:center;padding-top:100px;'><h2>BAŞVURUNUZ ALINDI.</h2><p>Loxy010 incelemesi sonrası Gmail ile dönüş yapılacaktır.</p><a href='/'>Ana Sayfa</a></body>"
    
    content = """
    <div class="container py-5">
        <div class="row justify-content-center">
            <div class="col-md-6 glass">
                <h3 class="mb-4 text-info">YETKİLİ KAYIT FORMU</h3>
                <form method="POST">
                    <input name="ad" class="input-custom" placeholder="Ad Soyad" required>
                    <input name="mail" class="input-custom" placeholder="Gmail Adresiniz" required>
                    <input name="is" class="input-custom" placeholder="Kurum / Görev" required>
                    <textarea name="neden" class="input-custom" placeholder="Erişim Nedeniniz?" rows="3"></textarea>
                    <button class="neon-btn w-100">BAŞVURUYU GÖNDER</button>
                </form>
            </div>
        </div>
    </div>
    """
    return render_template_string(LAYOUT, content=content)

@app.route("/dashboard")
def dashboard():
    if 'user' not in session: return redirect("/login")
    quakes = get_live_earthquakes()
    return render_template_string("""
    <!DOCTYPE html>
    <html lang="tr">
    <head>
        <meta charset="UTF-8">
        <title>DAKS v3.0 | Harekat Merkezi</title>
        <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
        <style>
            body { background: #020617; color: white; margin: 0; overflow: hidden; }
            .sidebar { height: 100vh; background: #0f172a; border-right: 1px solid #1e293b; overflow-y: auto; padding: 20px; }
            .quake-card { background: rgba(255,255,255,0.05); border: 1px solid #334155; padding: 10px; margin-bottom: 10px; cursor: pointer; border-radius: 8px; }
            .quake-card:hover { background: #1e293b; }
        </style>
    </head>
    <body>
        <div class="container-fluid">
            <div class="row">
                <div class="col-md-3 sidebar">
                    <h4 style="color:#38bdf8;">DAKS HAREKAT</h4>
                    <hr>
                    <a href="/admin_panel" class="btn btn-outline-info btn-sm w-100 mb-4">Gelen Kayıtları Yönet</a>
                    <h6 class="text-secondary small">CANLI DEPREMLER (Kandilli)</h6>
                    {% for q in quakes %}
                    <div class="quake-card" onclick="document.getElementById('m-frame').src='/map_gen?coords={{q.geojson.coordinates[1]}},{{q.geojson.coordinates[0]}}&mag={{q.mag}}'">
                        <strong>{{ q.title.split('(')[0] }}</strong> <span class="badge bg-danger">{{ q.mag }}</span><br>
                        <small class="text-muted">{{ q.date }}</small>
                    </div>
                    {% endfor %}
                </div>
                <div class="col-md-9 p-0">
                    <iframe id="m-frame" src="/map_init" style="width:100%; height:100vh; border:none;"></iframe>
                </div>
            </div>
        </div>
    </body>
    </html>
    """, quakes=quakes)

@app.route("/admin_panel")
def admin_panel():
    if 'user' not in session: return redirect("/login")
    return render_template_string("""
    <body style="background:#020617; color:white; padding:40px;">
        <h3>Gelen Yetki Başvuruları</h3>
        <table border="1" style="width:100%; margin-top:20px; text-align:left;">
            <tr><th>Ad</th><th>Mail</th><th>Görev</th><th>Neden</th></tr>
            {% for r in regs %}
            <tr><td>{{r.ad}}</td><td>{{r.mail}}</td><td>{{r.is}}</td><td>{{r.neden}}</td></tr>
            {% endfor %}
        </table>
        <br><a href="/dashboard">Geri Dön</a>
    </body>
    """, regs=pending_registrations)

@app.route("/map_init")
def map_init():
    return folium.Map(location=[39, 35], zoom_start=6, tiles="cartodb dark_matter")._repr_html_()

@app.route("/map_gen")
def map_gen():
    coords = request.args.get('coords')
    lat, lon = map(float, coords.split(','))
    mag = float(request.args.get('mag', 4))
    m = folium.Map(location=[lat, lon], zoom_start=11)
    folium.TileLayer('https://mt1.google.com/vt/lyrs=y&x={x}&y={y}&z={z}', name='Uydu', attr='Google').add_to(m)
    folium.TileLayer('cartodb dark_matter', name='Gece').add_to(m)
    folium.LayerControl().add_to(m)
    Fullscreen().add_to(m)
    
    heat_data = [[lat + random.gauss(0, 0.05), lon + random.gauss(0, 0.05), 0.7] for _ in range(200)]
    HeatMap(heat_data).add_to(m)
    folium.Marker([lat, lon], icon=folium.Icon(color='red', icon='info-sign')).add_to(m)
    return m._repr_html_()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)
