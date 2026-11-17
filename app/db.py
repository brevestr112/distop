import sqlite3
import time
from flask import g, current_app

SCHEMA = """
CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL UNIQUE COLLATE NOCASE,
    password_hash TEXT NOT NULL,
    bio TEXT DEFAULT '',
    status TEXT DEFAULT '',
    avatar TEXT DEFAULT '',
    banner TEXT DEFAULT '',
    frame TEXT DEFAULT 'frame-default',
    nick_color TEXT DEFAULT '#ffffff',
    chat_theme TEXT DEFAULT 'theme-default',
    avatar_effect TEXT DEFAULT 'effect-none',
    font_style TEXT DEFAULT 'font-default',
    bg_effect TEXT DEFAULT 'bg-none',
    banner_effect TEXT DEFAULT 'banner-none',
    points INTEGER DEFAULT 0,
    role TEXT DEFAULT 'user',
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
"""

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

def init_db(app):
    with app.app_context():
        db = get_db()
        db.executescript(SCHEMA)
        
        # Наполняем магазин
        if not db.execute("SELECT 1 FROM shop_items").fetchone():
            items = [
                # Рамки
                ("Золотая рамка", "Блестит", 50, "frame", "frame-gold"),
                ("Неоновая рамка", "Светится", 100, "frame", "frame-neon"),
                ("Огненная рамка", "Анимация огня", 150, "frame", "frame-fire"),
                ("Радужная рамка", "Переливается цветами", 250, "frame", "frame-rainbow"),
                # Темы чатов
                ("Тема Космос", "Темный космос", 100, "chat_theme", "theme-space"),
                ("Тема Матрица", "Зеленый код", 100, "chat_theme", "theme-matrix"),
                # Цвета ников
                ("Ник: Золотой", "Выделяйся", 80, "nick_color", "#f2c94c"),
                ("Ник: Неон", "Яркий голубой", 80, "nick_color", "#38bdf8"),
                # Эффекты аватарок
                ("Аватар: Пульс", "Аватарка дышит", 150, "avatar_effect", "effect-pulse"),
                ("Аватар: Вращение", "Медленно крутится", 200, "avatar_effect", "effect-spin"),
                # Шрифты
                ("Шрифт: Моно", "Стиль программиста", 120, "font_style", "font-mono"),
                ("Шрифт: Курсив", "Элегантный стиль", 120, "font_style", "font-italic"),
                # Фоны
                ("Фон: Аврора", "Плавные волны", 180, "bg_effect", "bg-aurora"),
                ("Фон: Туманность", "Космический фон", 180, "bg_effect", "bg-nebula"),
                # Баннеры
                ("Баннер: Свет", "Мигающий свет", 100, "banner_effect", "banner-glow"),
            ]
            db.executemany(
                "INSERT INTO shop_items (name, description, price, type, css_class, created) VALUES (?, ?, ?, ?, ?, ?)",
                [(i[0], i[1], i[2], i[3], i[4], int(time.time())) for i in items]
            )
        db.commit()