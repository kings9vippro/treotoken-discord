import os
import time
import threading
import requests
import json
from flask import Flask, request, redirect, render_template_string, jsonify
from flask_cors import CORS

app = Flask(__name__)
CORS(app) # Cho phép Userscript gọi API

TOKENS_FILE = 'tokens.json'
API_KEY = "KHOI_RENDER_SECRET_KEY_2024" # Mật khẩu bảo mật API (ông có thể đổi)

def load_tokens():
    if os.path.exists(TOKENS_FILE):
        with open(TOKENS_FILE, 'r') as f:
            return json.load(f)
    return {}

def save_tokens():
    with open(TOKENS_FILE, 'w') as f:
        json.dump(TOKENS, f)

TOKENS = load_tokens()

HTML = """
<!DOCTYPE html>
<html>
<head>
    <title>Ngâm Acc Discord 24/7</title>
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body { font-family: system-ui, sans-serif; background: #fff; color: #000; padding: 20px; max-width: 800px; margin: auto; }
        input, button { padding: 10px; border: 2px solid #000; font-size: 14px; margin: 5px 0; border-radius: 5px; }
        button { background: #000; color: #fff; cursor: pointer; font-weight: bold; transition: 0.2s; }
        button:hover { background: #333; }
        .token-box { border: 2px solid #000; padding: 15px; margin: 15px 0; border-radius: 8px; display: flex; justify-content: space-between; align-items: center; }
        .live { color: #fff; background: #000; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;}
        .die { color: #fff; background: #ff0000; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;}
        .wait { color: #000; background: #ccc; padding: 3px 10px; border-radius: 12px; font-size: 12px; font-weight: bold;}
        .info { font-size: 12px; color: #555; margin-bottom: 5px; }
    </style>
</head>
<body>
    <h2>HỆ THỐNG NGÂM ACC 24/7 (AUTO SYNC)</h2>
    <form action="/add" method="POST" style="display:flex; gap:10px;">
        <input type="text" name="token" placeholder="Dán Token Discord vào đây..." required style="flex:1;">
        <button type="submit">Thêm Thủ Công</button>
    </form>
    <hr style="border: 1px solid #000; margin: 20px 0;">
    <div>
        {% for token, data in tokens.items() %}
            <div class="token-box">
                <div>
                    <div class="info">User: <b>{{ data.user }}</b> | Mail: {{ data.email }}</div>
                    <div style="font-family:monospace; font-size:12px; word-break:break-all; margin-bottom:5px;">{{ token[:30] }}...</div>
                    <div>Trạng thái: 
                        {% if data.status == 'Live' %}<span class="live">Live (Sống)</span>
                        {% elif data.status == 'Die' %}<span class="die">Die (Chết)</span>
                        {% else %}<span class="wait">{{ data.status }}</span>{% endif %}
                    </div>
                </div>
                <form action="/delete/{{ token }}" method="POST">
                    <button type="submit" style="background:#fff; color:#ff0000; border-color:#ff0000;">Xóa</button>
                </form>
            </div>
        {% else %}
            <div style="text-align:center; color:#666;">Chưa có token nào. Hãy reg bằng tool hoặc thêm thủ công!</div>
        {% endfor %}
    </div>
</body>
</html>
"""

def keep_alive_loop():
    while True:
        for token in list(TOKENS.keys()):
            try:
                res = requests.get('https://discord.com/api/v9/users/@me', headers={'Authorization': token}, timeout=10)
                if res.status_code == 200:
                    TOKENS[token]['status'] = 'Live'
                elif res.status_code == 401:
                    TOKENS[token]['status'] = 'Die'
                else:
                    TOKENS[token]['status'] = f'Lỗi {res.status_code}'
            except Exception:
                TOKENS[token]['status'] = 'Lỗi mạng'
        save_tokens()
        time.sleep(45) 

threading.Thread(target=keep_alive_loop, daemon=True).start()

# API ĐỂ TOOL REG TRÊN ĐIỆN THOẠI BẮN TOKEN QUA
@app.route('/api/sync', methods=['POST'])
def api_sync():
    # Kiểm tra mật khẩu API
    if request.headers.get('X-API-KEY') != API_KEY:
        return jsonify({"error": "Sai API KEY"}), 401
    
    data = request.json
    token = data.get('token')
    email = data.get('email', 'Unknown')
    username = data.get('username', 'Unknown')
    
    if token:
        TOKENS[token] = {'email': email, 'user': username, 'status': 'Đang check...'}
        save_tokens()
        return jsonify({"status": "success", "message": "Đã thêm token!"}), 200
    return jsonify({"error": "Thiếu token"}), 400

@app.route('/')
def home():
    return render_template_string(HTML, tokens=TOKENS)

@app.route('/add', methods=['POST'])
def add():
    token = request.form.get('token')
    if token:
        TOKENS[token] = {'email': 'Thủ công', 'user': 'Thủ công', 'status': 'Đang check...'}
        save_tokens()
    return redirect('/')

@app.route('/delete/<token>', methods=['POST'])
def delete(token):
    if token in TOKENS:
        del TOKENS[token]
        save_tokens()
    return redirect('/')

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port)
