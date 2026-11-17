from functools import wraps
from flask import g, session, jsonify
from ..db import get_db


def login_required(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        uid = session.get('uid')
        if not uid:
            return jsonify(error="Не авторизован"), 401
        user = get_db().execute(
            "SELECT * FROM users WHERE id = ?", (uid,)
        ).fetchone()
        if not user:
            session.clear()
            return jsonify(error="Пользователь не найден"), 401
        if user['banned']:
            session.clear()
            return jsonify(error="Аккаунт заблокирован: " + (user['ban_reason'] or 'нарушение правил')), 403
        g.user = user
        return f(*args, **kwargs)
    return wrapper