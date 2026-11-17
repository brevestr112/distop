from flask import Blueprint, jsonify, g
from ..db import get_db
from ..services.security import login_required
import time

bp = Blueprint('friends', __name__)

@bp.post('/api/friends/add/<username>')
@login_required
def add_friend(username):
    db = get_db()
    friend = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not friend or friend['id'] == g.user['id']:
        return jsonify(error="Нельзя добавить"), 400
        
    db.execute("INSERT OR IGNORE INTO friends (user_id, friend_id, status, created) VALUES (?, ?, 'pending', ?)",
               (g.user['id'], friend['id'], int(time.time())))
    db.commit()
    return jsonify(ok=True)

@bp.post('/api/friends/accept/<username>')
@login_required
def accept_friend(username):
    db = get_db()
    friend = db.execute("SELECT id FROM users WHERE username = ?", (username,)).fetchone()
    if not friend: return jsonify(error="Не найден"), 404
        
    # Подтверждаем запрос от друга
    db.execute("UPDATE friends SET status = 'accepted' WHERE user_id = ? AND friend_id = ?",
               (friend['id'], g.user['id']))
    # Создаем ответную запись
    db.execute("INSERT OR IGNORE INTO friends (user_id, friend_id, status, created) VALUES (?, ?, 'accepted', ?)",
               (g.user['id'], friend['id'], int(time.time())))
    db.commit()
    return jsonify(ok=True)