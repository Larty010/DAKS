from flask import Flask, render_template_string, request
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor

app = Flask(__name__)

# --- 1. YAPAY ZEKA MOTORU ---
# Uygulama açıldığında bir kez eğitilir ve hazır bekler
def train_model():
    # Modelin öğrenmesi için 1000 satırlık sentetik veri
    n = 1000
    data = {
        'mag': np.random.uniform(4, 8, n),        # Deprem Büyüklüğü
        'derinlik': np.random.uniform(5, 30, n),   # Odak Derinliği
        'zemin': np.random.randint(1, 5, n),      # Zemin Sınıfı (1:Sert - 4:Yumuşak)
        'bina_yasi': np.random.uniform(0, 50, n)   # Bina Yaşı
    }
    X = pd.DataFrame(data)
    
    # Bilimsel temelli Hasar Riski (Hedef Değişken)
    # Formül: (Büyüklük * 0.5) + (Zemin * 0.2) + (Yaş * 0.05) - (Derinlik * 0.02)
    y = (X['mag'] * 0.5) + (X['zemin'] * 0.2) + (X['bina_yasi'] * 0.05) - (X['derinlik'] * 0.02)
    y = (y - y.min()) / (y.max() - y.min()) # 0 ile 1 arasına sabitle
    
    model = RandomForestRegressor(n_estimators=50, random_state=42)
    model.fit(X, y)
    return model

# Uygulama başlarken modeli eğit
print("AI Modeli eğitiliyor...")
ai_asistan = train_model()

# --- 2. GÖRSEL ARAYÜZ (Modern UI Tasarımı) ---
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="tr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Deprem AI | Asistan</title>
    <style>
        :root { --primary: #3b82f6; --bg: #0f172a; --card: #1e293b; }
        body { font-family: 'Segoe UI', sans-serif; background: var(--bg); color: white; margin: 0; padding: 20px; display: flex; justify-content: center; }
        .app-container { width: 100%; max-width: 500px; background: var(--card); border-radius: 20px; padding: 25px; box-shadow: 0 10px 30px rgba(0,0,0,0.5); }
        h1 { color: var(--primary); text-align: center; font-size: 1.5rem; margin-bottom: 20px; }
        .input-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; font-size: 0.9rem; color: #94a3b8; }
        input { width: 100%; padding: 12px; border-radius: 10px; border: 1px solid #334155; background: #0f172a; color: white; box-sizing: border-box; }
        button { width: 100%; padding: 15px; background: var(--primary); color: white; border: none; border-radius: 10px; font-weight: bold; cursor: pointer; transition: 0.3s; margin-top: 10px; }
        button:hover { background: #2563eb; transform: translateY(-2px); }
        .result-box { margin-top: 25px; padding: 15px; border-radius: 12px; background: #0f172a; border-left: 5px solid var(--primary); display: {{ display }}; }
        .risk-value { font-size: 1.8rem; font-weight: bold; color: #fb7185; }
        .advice { margin-top: 10px; font-style: italic; color: #cbd5e1; font-size: 0.9rem; }
    </style>
</head>
<body>
    <div class="app-container">
        <h1>🤖 Deprem AI Asistanı</h1>
        <form method="POST">
            <div class="input-group">
                <label>Deprem Büyüklüğü (Mw)</label>
                <input type="number" step="0.1" name="mag" value="7.4" required>
            </div>
            <div class="input-group">
                <label>Odak Derinliği (km)</label>
                <input type="number" name="derinlik" value="10" required>
            </div>
            <div class="input-group">
                <label>Bina Yaşı (Ortalama)</label>
                <input type="number" name="yas" value="25" required>
            </div>
            <div class="input-group">
                <label>Zemin Kalitesi (1: En İyi, 4: En Kötü)</label>
                <input type="number" min="1" max="4" name="zemin" value="3" required>
            </div>
            <button type="submit">Analizi Başlat</button>
        </form>

        <div class="result-box">
            <strong>Analiz Raporu:</strong><br>
            <div class="risk-value">%{{ risk }}</div>
            <p>Hasar Olasılığı Tahmini</p>
            <div class="advice">💬 Tavsiye: {{ tavsiye }}</div>
        </div>
    </div>
</body>
</html>
"""

# --- 3. UYGULAMA MANTIĞI (Rotalar) ---
@app.route("/", methods=["GET", "POST"])
def index():
    risk = 0
    display = "none"
    tavsiye = ""
    
    if request.method == "POST":
        # Formdan gelen verileri al
        mag = float(request.form.get("mag"))
        der = float(request.form.get("derinlik"))
        yas = float(request.form.get("yas"))
        zem = float(request.form.get("zemin"))
        
        # Yapay Zekadan tahmin iste
        input_data = pd.DataFrame([[mag, der, zem, yas]], columns=['mag', 'derinlik', 'zemin', 'bina_yasi'])
        prediction = ai_asistan.predict(input_data)[0]
        
        risk = round(prediction * 100, 1)
        display = "block"
        
        # Akıllı Tavsiye Üret
        if risk > 75:
            tavsiye = "Kritik seviye! Bu bölgedeki binalar için acil tahliye ve güçlendirme planları incelenmelidir."
        elif risk > 45:
            tavsiye = "Risk orta-yüksek seviyede. Deprem sonrası ilk yardım ekiplerinin bu koordinatlara yönlendirilmesi önerilir."
        else:
            tavsiye = "Risk düşük görünmekle birlikte, sarsıntı sismik yorgunluğa neden olabilir. Saha kontrolü yapılmalıdır."

    return render_template_string(HTML_TEMPLATE, risk=risk, display=display, tavsiye=tavsiye)

if __name__ == "__main__":
    # İnternete yüklendiğinde çalışması için host="0.0.0.0"
    app.run(host="0.0.0.0", port=5000)
