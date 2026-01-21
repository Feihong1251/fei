from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import logging
import os
import sys

# --- ส่วนที่แก้ไข 1: การตั้งค่า Log ---
# เปลี่ยนจากเขียนลงไฟล์ system.log เป็นเขียนลง Console (sys.stdout)
# เพื่อไม่ให้เกิด Error Permission Denied บน Vercel
logging.basicConfig(
    stream=sys.stdout, 
    level=logging.INFO, 
    format='%(asctime)s - %(levelname)s - %(message)s'
)

app = Flask(__name__)
app.secret_key = 'my_secret_key'

# --- ส่วนที่แก้ไข 2: เส้นทาง Database ---
# ถ้าอยู่บน Vercel ให้ใช้โฟลเดอร์ชั่วคราว /tmp
# ถ้าอยู่ในเครื่องเรา ให้ใช้โฟลเดอร์ปัจจุบัน
if 'VERCEL' in os.environ:
    DB_PATH = '/tmp/database.db'
else:
    DB_PATH = 'database.db'

def get_db_connection():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    ''')
    conn.commit()
    conn.close()

# เรียกสร้างตารางทุกครั้ง เพราะใน Vercel โฟลเดอร์ /tmp อาจถูกลบเมื่อไหร่ก็ได้
init_db()

@app.route('/')
def index():
    if 'username' in session:
        return redirect(url_for('home'))
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            # ตรวจสอบว่ามีตารางหรือยัง (กันเหนียวสำหรับ Vercel)
            init_db()
            
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                         (username, password))
            conn.commit()
            conn.close()
            
            logging.info(f'สมัครสมาชิกสำเร็จ: {username}') 
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            logging.warning(f'สมัครสมาชิกไม่สำเร็จ (ชื่อซ้ำ): {username}')
            return "Username นี้มีคนใช้แล้วครับ กรุณาใช้ชื่ออื่น"
        except Exception as e:
            logging.error(f"Error Register: {e}")
            return "เกิดข้อผิดพลาดบางอย่าง"

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        try:
            conn = get_db_connection()
            user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                                (username, password)).fetchone()
            conn.close()
            
            if user:
                session['username'] = user['username']
                logging.info(f'เข้าสู่ระบบสำเร็จ: {username}')
                return redirect(url_for('home'))
            else:
                logging.warning(f'พยายามเข้าสู่ระบบผิดพลาด: {username}')
                return "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง!"
        except Exception as e:
            logging.error(f"Error Login: {e}")
            return "เกิดข้อผิดพลาดในการเชื่อมต่อฐานข้อมูล"

    return render_template('login.html')

@app.route('/home')
def home():
    if 'username' in session:
        return render_template('home.html', name=session['username'])
    else:
        return redirect(url_for('login'))

@app.route('/logout')
def logout():
    user = session.get('username')
    session.pop('username', None)
    if user:
        logging.info(f'ออกจากระบบ: {user}')
    return redirect(url_for('login'))

# บรรทัดนี้จำเป็นสำหรับ Vercel
app = app