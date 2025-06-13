from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
import paho.mqtt.client as mqtt
import json
from datetime import datetime
from functools import wraps
import os
import sqlite3
from werkzeug.security import generate_password_hash, check_password_hash
import io
import base64
import matplotlib
matplotlib.use('Agg')  # 必须加，防止 Flask 环境下报错
import matplotlib.pyplot as plt
import numpy as np
from matplotlib.dates import DateFormatter
from openai import OpenAI

app = Flask(__name__)
app.secret_key = 'your-secret-key-here'  # 请更改为一个安全的密钥

# OpenAI API 配置
from openai import OpenAI
client = OpenAI(
    base_url="https://api.gptapi.us/v1",
    api_key="sk-Ewv4n5AcG7qB66nmBeCd23516bBe40839d87A03b6c5368Ac"
)

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

DB_PATH = os.path.join(os.path.dirname(__file__), '..', 'smart_garden', 'garden_sensor_data.db')

def get_latest_db_data():
    """从数据库获取最新一条传感器数据"""
    try:
        print(f"📂 尝试连接数据库: {DB_PATH}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SensorData'")
        if not cursor.fetchone():
            print("❌ 数据库表不存在，创建新表...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS SensorData (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Timestamp TEXT,
                    Humidity REAL,
                    DroughtAlert INTEGER,
                    Light REAL,
                    PH REAL,
                    Rain INTEGER,
                    CO2 REAL
                )
            ''')
            conn.commit()
            print("✅ 数据库表创建成功")
            return None

        # 获取最新数据
        cursor.execute('''
            SELECT Timestamp, Humidity, DroughtAlert, Light, PH, Rain, CO2 
            FROM SensorData 
            ORDER BY ID DESC LIMIT 1
        ''')
        row = cursor.fetchone()
        conn.close()

        if row:
            print("✅ 成功获取最新数据")
            return {
                "timestamp": row[0],
                "humidity": row[1],
                "drought_alert": bool(row[2]),
                "light": row[3],
                "ph": row[4],
                "rain": bool(row[5]),
                "co2": row[6],
                "last_update": datetime.now().strftime("%H:%M:%S")
            }
        else:
            print("⚠️ 数据库中没有数据")
            return None

    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")
        return None
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return None

def get_history_data(limit=50):
    """获取历史数据"""
    try:
        print(f"📂 尝试获取历史数据，限制: {limit}")
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SensorData'")
        if not cursor.fetchone():
            print("❌ 数据库表不存在")
            return []

        cursor.execute('''
            SELECT Timestamp, Humidity, DroughtAlert, Light, PH, Rain, CO2
            FROM SensorData
            ORDER BY ID DESC
            LIMIT ?
        ''', (limit,))
        rows = cursor.fetchall()
        conn.close()

        # 转换为字典列表，统一时间格式
        history = []
        for row in rows:
            try:
                # 尝试解析时间戳
                if 'T' in row[0]:  # ISO格式
                    timestamp = datetime.fromisoformat(row[0]).strftime("%Y-%m-%d %H:%M:%S")
                else:  # 标准格式
                    timestamp = datetime.strptime(row[0], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            except (ValueError, TypeError):
                # 如果解析失败，使用原始时间戳
                timestamp = row[0]

            history.append({
                'timestamp': timestamp,
                'humidity': row[1],
                'drought_alert': bool(row[2]),
                'light': row[3],
                'ph': row[4],
                'rain': bool(row[5]),
                'co2': row[6]
            })
        
        print(f"✅ 成功获取 {len(history)} 条历史数据")
        return history

    except sqlite3.Error as e:
        print(f"❌ 数据库错误: {e}")
        return []
    except Exception as e:
        print(f"❌ 未知错误: {e}")
        return []

def save_sensor_data(data):
    """保存传感器数据到数据库"""
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        # 检查表是否存在
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='SensorData'")
        if not cursor.fetchone():
            print("创建传感器数据表...")
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS SensorData (
                    ID INTEGER PRIMARY KEY AUTOINCREMENT,
                    Timestamp TEXT,
                    Humidity REAL,
                    DroughtAlert INTEGER,
                    Light REAL,
                    PH REAL,
                    Rain INTEGER,
                    CO2 REAL
                )
            ''')
            conn.commit()
        
        # 统一时间戳格式
        try:
            # 尝试解析时间戳
            if 'timestamp' in data:
                if 'T' in data['timestamp']:  # ISO格式
                    # 将UTC时间转换为本地时间
                    utc_time = datetime.fromisoformat(data['timestamp'])
                    timestamp = utc_time.strftime("%Y-%m-%d %H:%M:%S")
                else:  # 标准格式
                    timestamp = datetime.strptime(data['timestamp'], "%Y-%m-%d %H:%M:%S").strftime("%Y-%m-%d %H:%M:%S")
            else:
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        except (ValueError, TypeError):
            # 如果解析失败，使用当前时间
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # 检查是否已存在相同时间戳的数据
        cursor.execute('SELECT COUNT(*) FROM SensorData WHERE Timestamp = ?', (timestamp,))
        if cursor.fetchone()[0] > 0:
            print(f"⚠️ 已存在时间戳为 {timestamp} 的数据，跳过保存")
            return
        
        # 插入新数据
        cursor.execute('''
            INSERT INTO SensorData (Timestamp, Humidity, DroughtAlert, Light, PH, Rain, CO2)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        ''', (
            timestamp,
            data.get('humidity', 0),
            1 if data.get('humidity', 0) < 40 else 0,
            data.get('light', 0),
            data.get('ph', 0),
            1 if data.get('rain', False) else 0,
            data.get('co2', 0)
        ))
        conn.commit()
        print(f"✅ 传感器数据已保存到数据库，时间戳: {timestamp}")
        
    except Exception as e:
        print(f"❌ 保存传感器数据时出错: {e}")
    finally:
        if conn:
            conn.close()

# ========== 实时监测图数据缓存 ==========
plot_data_history = {
    'timestamp': [],
    'co2': [],
    'ph': [],
    'humidity': [],
    'light': []
}
PLOT_MAX_POINTS = 50

def update_plot_data(new_data):
    from datetime import datetime
    plot_data_history['timestamp'].append(datetime.now())
    if len(plot_data_history['timestamp']) > PLOT_MAX_POINTS:
        plot_data_history['timestamp'].pop(0)
    for key in ['co2', 'ph', 'humidity', 'light']:
        plot_data_history[key].append(new_data.get(key, 0))
        if len(plot_data_history[key]) > PLOT_MAX_POINTS:
            plot_data_history[key].pop(0)

# ========== MQTT Callbacks ==========
def on_connect(client, userdata, flags, rc, properties=None):
    if rc == 0:
        print("✅ 成功连接到MQTT代理！")
        client.subscribe(TOPIC)
        print(f"✅ 已订阅主题: {TOPIC}")
    else:
        print(f"❌ 连接失败，错误代码: {rc}")

def on_message(client, userdata, msg):
    global sensor_data
    try:
        data = json.loads(msg.payload.decode())

        # 统一时间格式处理
        try:
            # 尝试解析ISO格式时间
            utc_time = datetime.fromisoformat(data["timestamp"])
        except (ValueError, TypeError):
            # 如果不是ISO格式，尝试其他常见格式
            try:
                utc_time = datetime.strptime(data["timestamp"], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                # 如果都失败，使用当前时间
                utc_time = datetime.now()

        # 统一转换为本地时间字符串格式
        local_time = utc_time.strftime("%Y-%m-%d %H:%M:%S")

        # Update all sensor data in memory
        sensor_data.update({
            "timestamp": local_time,
            "humidity": data["humidity"],
            "drought_alert": data["humidity"] < 40,  # 当湿度低于40%时触发干旱警报
            "light": data["light"],
            "ph": data["ph"],
            "rain": data["rain"],
            "co2": data["co2"],
            "last_update": datetime.now().strftime("%H:%M:%S")
        })
        
        # 更新绘图数据
        update_plot_data(data)
        print(f"✅ 数据已更新: {sensor_data}")

    except Exception as e:
        print(f"❌ 数据处理错误: {e}")

# ========== MQTT Client Setup ==========
mqtt_client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.on_connect = on_connect
mqtt_client.on_message = on_message

try:
    print("正在连接MQTT服务器...")
    mqtt_client.connect(BROKER, PORT, 60)
    mqtt_client.loop_start()
except Exception as e:
    print(f"⚠️ MQTT连接错误: {e}")

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

@app.route('/history')
def history():
    if 'username' not in session:
        return redirect(url_for('login'))
    return render_template('history.html')

@app.route('/api/history')
@login_required
def api_history():
    """返回历史数据"""
    history = get_history_data(limit=50)
    return jsonify(history)

@app.route('/api/latest')
@login_required
def api_latest():
    """返回最新的传感器数据"""
    return jsonify(sensor_data)

# ========== 实时监测图接口 ==========
@app.route('/plot.png')
@login_required
def plot_png():
    """生成实时监测图表"""
    history = get_history_data(limit=50)
    if not history or len(history) < 2:
        plt.figure(figsize=(12, 8))
        plt.text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=20)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        return app.response_class(buf.getvalue(), mimetype='image/png')

    # 按时间升序排列
    history = list(reversed(history))
    ts, co2, ph, humidity, light = [], [], [], [], []
    for row in history:
        try:
            ts.append(datetime.fromisoformat(row['timestamp']))
            co2.append(row['co2'])
            ph.append(row['ph'])
            humidity.append(row['humidity'])
            light.append(row['light'])
        except Exception as e:
            print("数据格式错误：", row, e)
            continue

    # 检查数据长度
    if not (len(ts) and len(co2) and len(ph) and len(humidity) and len(light)):
        plt.figure(figsize=(12, 8))
        plt.text(0.5, 0.5, 'No Data', ha='center', va='center', fontsize=20)
        buf = io.BytesIO()
        plt.savefig(buf, format='png')
        plt.close()
        buf.seek(0)
        return app.response_class(buf.getvalue(), mimetype='image/png')

    THRESHOLDS = {
        'co2': {'low': 800, 'high': 1200},
        'ph': {'low': 6.0, 'high': 7.0},
        'humidity': {'low': 30, 'high': 80},
        'light': {'low': 500, 'high': 2000}
    }

    plt.figure(figsize=(12, 8))
    # --- CO2 ---
    plt.subplot(2, 2, 1)
    plt.plot(ts, co2, 'b-', linewidth=2, label='CO2 Level')
    plt.axhline(y=THRESHOLDS['co2']['low'], color='y', linestyle='--', label='Low Threshold')
    plt.axhline(y=THRESHOLDS['co2']['high'], color='r', linestyle='--', label='High Threshold')
    for i, val in enumerate(co2):
        if val < THRESHOLDS['co2']['low']:
            plt.scatter(ts[i], val, color='yellow', s=60, zorder=5)
        elif val > THRESHOLDS['co2']['high']:
            plt.scatter(ts[i], val, color='red', s=60, zorder=5)
    plt.title('CO2 Concentration Monitoring')
    plt.ylabel('CO2 (ppm)')
    plt.ylim(500, 2000)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # --- pH ---
    plt.subplot(2, 2, 2)
    plt.plot(ts, ph, 'g-', linewidth=2, label='pH Level')
    plt.axhline(y=THRESHOLDS['ph']['low'], color='r', linestyle='--', label='Low Threshold')
    plt.axhline(y=THRESHOLDS['ph']['high'], color='y', linestyle='--', label='High Threshold')
    for i, val in enumerate(ph):
        if val < THRESHOLDS['ph']['low']:
            plt.scatter(ts[i], val, color='red', s=60, zorder=5)
        elif val > THRESHOLDS['ph']['high']:
            plt.scatter(ts[i], val, color='yellow', s=60, zorder=5)
    plt.title('pH Level Monitoring')
    plt.ylabel('pH Value')
    plt.ylim(4, 10)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # --- Humidity ---
    plt.subplot(2, 2, 3)
    plt.plot(ts, humidity, 'm-', linewidth=2, label='Humidity')
    plt.axhline(y=30, color='r', linestyle='--', label='Low Threshold')
    plt.axhline(y=80, color='r', linestyle='--', label='High Threshold')
    for i, val in enumerate(humidity):
        if val < 30 or val > 80:
            plt.scatter(ts[i], val, color='red', s=60, zorder=5)
    plt.title('Humidity Monitoring')
    plt.ylabel('Humidity (%)')
    plt.ylim(0, 100)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # --- Light ---
    plt.subplot(2, 2, 4)
    plt.plot(ts, light, color='orange', linewidth=2, label='Light Level')
    plt.axhline(y=THRESHOLDS['light']['low'], color='r', linestyle='--', label='Low Threshold')
    plt.title('Light Level Monitoring')
    plt.ylabel('Light (lux)')
    plt.ylim(0, 3000)
    plt.grid(True, alpha=0.3)
    plt.legend()

    # 格式化x轴
    date_form = DateFormatter("%H:%M:%S")
    for i in range(1, 5):
        plt.subplot(2, 2, i)
        plt.gca().xaxis.set_major_formatter(date_form)
        plt.gca().tick_params(axis='x', rotation=45)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png')
    plt.close()
    buf.seek(0)
    return app.response_class(buf.getvalue(), mimetype='image/png')

@app.route('/gpt_prediction')
@login_required
def gpt_prediction():
    return render_template('prediction.html')

@app.route('/api/predict')
@login_required
def predict():
    try:
        # Get historical data
        history = get_history_data(limit=50)
        if not history:
            return jsonify({'prediction': 'No data available for analysis.'})

        # Prepare data summary
        data_summary = {
            'humidity': [h['humidity'] for h in history],
            'light': [h['light'] for h in history],
            'ph': [h['ph'] for h in history],
            'co2': [h['co2'] for h in history]
        }

        # Calculate trends
        trends = {}
        for key, values in data_summary.items():
            if len(values) >= 2:
                change = values[-1] - values[0]
                trends[key] = 'increasing' if change > 0 else 'decreasing' if change < 0 else 'stable'

        # Build prompt
        prompt = f"""Based on the following smart garden sensor data, please analyze the current trends and predict future trends:
        Humidity trend: {trends.get('humidity', 'unknown')}
        Light trend: {trends.get('light', 'unknown')}
        pH trend: {trends.get('ph', 'unknown')}
        CO2 concentration trend: {trends.get('co2', 'unknown')}
        
        Please briefly analyze the current situation, predict the possible trend for the next 50 data points, and provide 2-3 specific improvement suggestions. Respond in English."""

        # Call API using new OpenAI client format
        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "You are a professional smart garden advisor, skilled at analyzing sensor data and providing recommendations."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=200
        )

        prediction = response.choices[0].message.content
        
        return jsonify({
            'prediction': prediction,
        })

    except Exception as e:
        print(f"Prediction error: {e}")
        return jsonify({'prediction': f'Prediction service is temporarily unavailable. Error: {str(e)}'})

@app.route('/chart')
@login_required
def chart():
    return render_template('chart.html')

if __name__ == '__main__':
    try:
        print("\n🌱 智能花园监控系统正在启动...")
        
        # 确保数据库连接正常
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.close()
            print("✅ 数据库连接正常")
        except Exception as e:
            print(f"❌ 数据库连接错误: {e}")
        
        # 启动Flask应用
        app.run(host='0.0.0.0', port=5005, debug=True, threaded=True)
    except Exception as e:
        print(f"❌ 启动失败: {e}")