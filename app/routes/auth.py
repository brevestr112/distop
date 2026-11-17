from flask import Blueprint, request, jsonify, session, g
from werkzeug.security import generate_password_hash, check_password_hash
from ..db import get_db
from ..services.security import login_required
import time, os

bp = Blueprint('auth', __name__)

@bp.post('/api/register')
def register():
    data = request.json
    username = data.get('username', '').strip()
    password = data.get('password', '')
    if len(username) < 3 or len(password) < 6:
        return jsonify(error="Имя от 3 символов, пароль от 6"), 400
    
    db = get_db()
    try:
        role = 'creator' if username == os.environ.get('OWNER_USERNAME', 'admin') else 'user'
        cur = db.execute("INSERT INTO users (username, password_hash, role, created) VALUES (?, ?, ?, ?)",
                         (username, generate_password_hash(password), role, int(time.time())))
        db.commit()
        session['uid'] = cur.lastrowid
        return jsonify(ok=True)
    except Exception:
        return jsonify(error="Имя занято"), 400

@bp.post('/api/login')
def login():
    data = request.json
    user = get_db().execute("SELECT * FROM users WHERE username = ?", (data.get('username'),)).fetchone()
    if user and check_password_hash(user['password_hash'], data.get('password', '')):
        session['uid'] = user['id']
        return jsonify(ok=True)
    return jsonify(error="Неверный логин или пароль"), 401

@bp.post('/api/logout')
def logout():
    session.clear()
    return jsonify(ok=True)

@bp.get('/api/me')
@login_required
def me():
    return jsonify(user={
        "id": g.user['id'], "username": g.user['username'], "points": g.user['points'], 
        "frame": g.user['frame'], "avatar": g.user['avatar'], "banner": g.user['banner'],
        "bio": g.user['bio'], "role": g.user['role'], "nick_color": g.user['nick_color'],
        "chat_theme": g.user['chat_theme'], "avatar_effect": g.user['avatar_effect'],
        "font_style": g.user['font_style'], "status": g.user['status'],
        "bg_effect": g.user['bg_effect'], "banner_effect": g.user['banner_effect']
    })

@bp.get('/api/users')
@login_required
def get_users():
    q = request.args.get('q', '').strip()
    db = get_db()
    if q:
        users = db.execute("SELECT username, avatar, frame, role, nick_color FROM users WHERE username LIKE ?", (f'%{q}%',)).fetchall()
    else:
        users = db.execute("SELECT username, avatar, frame, role, nick_color FROM users").fetchall()
    return jsonify(users=[dict(u) for u in users])

@bp.post('/api/profile/update')
@login_required
def update_profile():
    data = request.json
    bio = data.get('bio', '')[:200]
    avatar = data.get('avatar', '')
    banner = data.get('banner', '')
    status = data.get('status', '')[:50]
    db = get_db()
    db.execute("UPDATE users SET bio = ?, avatar = ?, banner = ?, status = ? WHERE id = ?", 
               (bio, avatar, banner, status, g.user['id']))
    db.commit()
    return jsonify(ok=True)