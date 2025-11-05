
import sqlite3

DB_NAME = "takebook.db"

def get_conn():
    return sqlite3.connect(DB_NAME)

def create_tables():
    conn = get_conn()
    cur = conn.cursor()

    # Users table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            email TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')

    # Posts table
    cur.execute('''
        CREATE TABLE IF NOT EXISTS posts (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            author TEXT NOT NULL,
            content TEXT,
            image_path TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY(author) REFERENCES users(email)
        )
    ''')

    conn.commit()
    conn.close()


def add_user(email, password):
    conn = get_conn()
    cur = conn.cursor()
    try:
        cur.execute("INSERT INTO users (email, password) VALUES (?, ?)", (email, password))
        conn.commit()
        return True
    except sqlite3.IntegrityError:
        return False
    finally:
        conn.close()

def verify_user(email, password):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT * FROM users WHERE email=? AND password=?", (email, password))
    row = cur.fetchone()
    conn.close()
    return row is not None


def add_post(author, content, image_path=None):
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("INSERT INTO posts (author, content, image_path) VALUES (?, ?, ?)", (author, content, image_path))
    conn.commit()
    conn.close()

def get_posts():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute("SELECT author, content, image_path, created_at FROM posts ORDER BY id DESC")
    rows = cur.fetchall()
    conn.close()
    return rows
