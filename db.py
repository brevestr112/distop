import sqlite3
import time
from flask import g, current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    bio TEXT DEFAULT '',
    avatar TEXT DEFAULT '',
    banner TEXT DEFAULT '',
    frame TEXT DEFAULT 'default',
    chat_theme TEXT DEFAULT 'default',
    points INTEGER DEFAULT 0,
    role TEXT DEFAULT 'user',
    banned INTEGER DEFAULT 0,
    ban_reason TEXT DEFAULT '',
    daily_points INTEGER DEFAULT 0,
    last_points_date TEXT DEFAULT '',
    created INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS posts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    created INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS shop_items (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    description TEXT,
    price INTEGER NOT NULL,
    type TEXT NOT NULL,
    css_class TEXT,
    created INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS purchases (
    user_id INTEGER NOT NULL,
    item_id INTEGER NOT NULL,
    created INTEGER NOT NULL,
    PRIMARY KEY (user_id, item_id)
);
CREATE TABLE IF NOT EXISTS messages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sender_id INTEGER NOT NULL,
    recipient_id INTEGER NOT NULL,
    text TEXT NOT NULL,
    created INTEGER NOT NULL,
    read_at INTEGER
);
CREATE TABLE IF NOT EXISTS friends (
    user_id INTEGER NOT NULL,
    friend_id INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    created INTEGER NOT NULL,
    PRIMARY KEY (user_id, friend_id)
);
CREATE TABLE IF NOT EXISTS reports (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    reporter_id INTEGER NOT NULL,
    target_user_id INTEGER,
    post_id INTEGER,
    reason TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    created INTEGER NOT NULL
);
CREATE TABLE IF NOT EXISTS admin_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    admin_id INTEGER NOT NULL,
    action TEXT NOT NULL,
    target TEXT DEFAULT '',
    details TEXT DEFAULT '',
    created INTEGER NOT NULL
);
"""

MIGRATIONS = {
    'users': [
        ('banner', "TEXT DEFAULT ''"),
        ('chat_theme', "TEXT DEFAULT 'default'"),
        ('role', "TEXT DEFAULT 'user'"),
        ('banned', "INTEGER DEFAULT 0"),
        ('ban_reason', "TEXT DEFAULT ''"),
        ('daily_points', "INTEGER DEFAULT 0"),
        ('last_points_date', "TEXT DEFAULT ''"),
    ],
}


def get_db():
    if 'db' not in g:
        g.db = sqlite3.connect(current_app.config['DB_PATH'])
        g.db.row_factory = sqlite3.Row
        g.db.execute("PRAGMA foreign_keys = ON")
    return g.db


def close_db(e=None):
    db = g.pop('db', None)
    if db is not None:
        db.close()


def _migrate(db):
    for table, cols in MIGRATIONS.items():
        existing = {r[1] for r in db.execute(f"PRAGMA table_info({table})").fetchall()}
        for name, ddl in cols:
            if name not in existing:
                db.execute(f"ALTER TABLE {table} ADD COLUMN {name} {ddl}")


def init_db(app):
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        _migrate(db)
        if not db.execute("SELECT 1 FROM shop_items").fetchone():
            items = [
                ("Золотая рамка", "Блестит", 50, "frame", "frame-gold"),
                ("Неоновая рамка", "Светится", 100, "frame", "frame-neon"),
                ("Огненная рамка", "Анимация огня", 150, "frame", "frame-fire"),
                ("Космическая", "Звездный вихрь", 200, "frame", "frame-space"),
                ("Радужная рамка", "Переливается", 250, "frame", "frame-rainbow"),
                ("Тема Киберпанк", "Неоновый чат", 100, "theme", "theme-cyberpunk"),
                ("Тема Лес", "Зеленый чат", 100, "theme", "theme-forest"),
                ("Тема Закат", "Теплый чат", 100, "theme", "theme-sunset"),
            ]
            db.executemany(
                "INSERT INTO shop_items (name, description, price, type, css_class, created) VALUES (?,?,?,?,?,?)",
                [(i[0], i[1], i[2], i[3], i[4], int(time.time())) for i in items],
            )
        db.commit()