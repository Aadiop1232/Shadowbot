# database.py
import sqlite3
import datetime
import logging

DB_NAME = 'bot.db'
logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        role TEXT,
        join_date TEXT,
        language TEXT,
        points INTEGER DEFAULT 0,
        verified INTEGER DEFAULT 0,
        referrals INTEGER DEFAULT 0,
        banned INTEGER DEFAULT 0
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS platforms (
        platform_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS stock (
        stock_id INTEGER PRIMARY KEY AUTOINCREMENT,
        platform_id INTEGER,
        account_details TEXT,
        is_claimed INTEGER DEFAULT 0,
        FOREIGN KEY (platform_id) REFERENCES platforms(platform_id)
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS referrals (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        referrer_id INTEGER,
        referred_id INTEGER,
        points_earned INTEGER,
        timestamp TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS keys (
        key TEXT PRIMARY KEY,
        type TEXT,
        points_value INTEGER,
        is_claimed INTEGER DEFAULT 0
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS admin_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        action TEXT,
        timestamp TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS user_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        action TEXT,
        timestamp TEXT
    )
    ''')
    c.execute('''
    CREATE TABLE IF NOT EXISTS admins (
        user_id INTEGER PRIMARY KEY,
        role TEXT
    )
    ''')
    conn.commit()
    conn.close()

def add_user(user_id, username):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    join_date = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    try:
        c.execute(
            "INSERT OR IGNORE INTO users (user_id, username, role, join_date, language, points, verified, referrals, banned) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (user_id, username, 'user', join_date, 'en', 0, 0, 0, 0)
        )
    except Exception as e:
        logger.error(f"Error adding user {user_id}: {e}")
    conn.commit()
    conn.close()

def mark_user_verified(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET verified = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def update_user_language(user_id, language):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
    conn.commit()
    conn.close()

def get_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
    user = c.fetchone()
    conn.close()
    return user

def add_admin_log(admin_id, action):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO admin_logs (admin_id, action, timestamp) VALUES (?, ?, ?)",
              (admin_id, action, timestamp))
    conn.commit()
    conn.close()

def add_user_log(user_id, action):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    c.execute("INSERT INTO user_logs (user_id, action, timestamp) VALUES (?, ?, ?)",
              (user_id, action, timestamp))
    conn.commit()
    conn.close()

def is_admin(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM admins WHERE user_id = ?", (user_id,))
    admin = c.fetchone()
    conn.close()
    return admin is not None

def is_owner(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("SELECT * FROM admins WHERE user_id = ? AND role = 'owner'", (user_id,))
    owner = c.fetchone()
    conn.close()
    return owner is not None

def add_admin(user_id, role='admin'):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("INSERT OR REPLACE INTO admins (user_id, role) VALUES (?, ?)", (user_id, role))
    conn.commit()
    conn.close()

def ban_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET banned = 1 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def unban_user(user_id):
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("UPDATE users SET banned = 0 WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def generate_key(key_type="normal", quantity=1):
    import random, string
    keys = []
    for _ in range(quantity):
        rand_str = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
        if key_type == "normal":
            key = f"NKEY-{rand_str}"
            points = 15
        else:
            key = f"PKEY-{rand_str}"
            points = 35
        conn = sqlite3.connect(DB_NAME)
        c = conn.cursor()
        c.execute(
            "INSERT INTO keys (key, type, points_value, is_claimed) VALUES (?, ?, ?, ?)",
            (key, key_type, points, 0)
        )
        conn.commit()
        conn.close()
        keys.append(key)
    return keys
    
