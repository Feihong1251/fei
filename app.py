from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import logging # 1. นำเข้า library สำหรับทำ Log

# 2. ตั้งค่า Log
# ข้อมูลจะถูกบันทึกในไฟล์ชื่อ system.log
# รูปแบบ: เวลา - ระดับความสำคัญ - ข้อความ
logging.basicConfig(filename='system.log', 
                    level=logging.INFO, 
                    format='%(asctime)s - %(levelname)s - %(message)s',
                    encoding='utf-8')

app = Flask(__name__)
app.secret_key = 'my_secret_key'

def get_db_connection():
    conn = sqlite3.connect('database.db')
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
            conn = get_db_connection()
            conn.execute('INSERT INTO users (username, password) VALUES (?, ?)',
                         (username, password))
            conn.commit()
            conn.close()
            
            # --- บันทึก Log เมื่อสมัครสำเร็จ ---
            logging.info(f'สมัครสมาชิกสำเร็จ: {username}') 
            return redirect(url_for('login'))
            
        except sqlite3.IntegrityError:
            # --- บันทึก Log เมื่อชื่อซ้ำ ---
            logging.warning(f'สมัครสมาชิกไม่สำเร็จ (ชื่อซ้ำ): {username}')
            return "Username นี้มีคนใช้แล้วครับ กรุณาใช้ชื่ออื่น"

    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        
        conn = get_db_connection()
        user = conn.execute('SELECT * FROM users WHERE username = ? AND password = ?',
                            (username, password)).fetchone()
        conn.close()
        
        if user:
            session['username'] = user['username']
            # --- บันทึก Log เมื่อล็อกอินผ่าน ---
            logging.info(f'เข้าสู่ระบบสำเร็จ: {username}')
            return redirect(url_for('home'))
        else:
            # --- บันทึก Log เมื่อล็อกอินผิด ---
            logging.warning(f'พยายามเข้าสู่ระบบผิดพลาด: {username}')
            return "ชื่อผู้ใช้หรือรหัสผ่านไม่ถูกต้อง!"

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
    
    # --- บันทึก Log เมื่อออกจากระบบ ---
    if user:
        logging.info(f'ออกจากระบบ: {user}')
        
    return redirect(url_for('login'))

if __name__ == '__main__':
    app.run(debug=True)