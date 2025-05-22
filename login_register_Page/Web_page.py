from flask import Flask, render_template, request, redirect, url_for, session, flash
import paho.mqtt.client as mqtt
import json
from datetime import datetime
from functools import wraps
import os
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 请更改为一个安全的密钥

# 用户数据文件
USERS_FILE = 'users.json'

# 确保用户数据文件存在
if not os.path.exists(USERS_FILE):
    with open(USERS_FILE, 'w') as f:
        json.dump({}, f)

def load_users():
    with open(USERS_FILE, 'r') as f:
        return json.load(f)

def save_users(users):
    with open(USERS_FILE, 'w') as f:
        json.dump(users, f)

# ========== 用户认证 ==========
def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'logged_in' not in session:
            return redirect(url_for('login'))
        return f(*args, **kwargs)
    return decorated_function

# ========== MQTT Configuration ==========
BROKER = "localhost"
PORT = 1883
TOPIC = "garden/sensors"  # Must match your publisher

# ========== Sensor Data Storage ==========
sensor_data = {
    "timestamp": "Waiting for data...",
    "humidity": 0,
    "drought_alert": False,
    "light": 0,
    "ph": 0,
    "rain": False,
    "co2": 0,
    "last_update": "Never updated"
}


# ========== MQTT Callbacks ==========
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ Successfully connected to MQTT broker!")
        client.subscribe(TOPIC)
    else:
        print(f"❌ Connection failed with code: {rc}")


def on_message(client, userdata, msg):
    global sensor_data
    try:
        data = json.loads(msg.payload.decode())

        # Convert timestamp to local time
        utc_time = datetime.fromisoformat(data["timestamp"])
        local_time = utc_time.astimezone().strftime("%Y-%m-%d %H:%M:%S")

        # Update all sensor data
        sensor_data.update({
            "timestamp": local_time,
            "humidity": data["humidity"],
            "drought_alert": data["drought_alert"],
            "light": data["light"],
            "ph": data["ph"],
            "rain": data["rain"],
            "co2": data["co2"],
            "last_update": datetime.now().strftime("%H:%M:%S")
        })

        print(f"Data received: {sensor_data}")

    except Exception as e:
        print(f"❌ Data processing error: {e}")


# ========== MQTT Client Setup ==========
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    mqtt_client.connect(BROKER, PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"⚠️ MQTT connection error: {e}")


# ========== Flask Routes ==========
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        users = load_users()
        
        # 验证用户名是否已存在
        if username in users:
            return render_template('register.html', error='Username already exists')

        # 验证密码
        if password != confirm_password:
            return render_template('register.html', error='Passwords do not match')

        # 创建新用户
        users[username] = generate_password_hash(password)
        save_users(users)

        flash('Registration successful! Please login')
        return redirect(url_for('login'))

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    error = None
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        users = load_users()
        if username in users and check_password_hash(users[username], password):
            session['logged_in'] = True
            session['username'] = username
            return redirect(url_for('index'))
        else:
            error = 'Invalid username or password'
    return render_template('login.html', error=error)

@app.route('/logout')
def logout():
    session.pop('logged_in', None)
    session.pop('username', None)
    return redirect(url_for('login'))

@app.route('/')
@login_required
def index():
    return render_template('index.html', data=sensor_data)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)