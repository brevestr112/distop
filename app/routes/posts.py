import time
from datetime import datetime
from flask import Blueprint, request, jsonify, g
from ..db import get_db
from ..services.security import login_required

bp = Blueprint('posts', __name__)
DAILY_LIMIT = 50


@bp.get('/api/posts')
@login_required
def get_posts():
    rows = get_db().execute("""
        SELECT p.id, p.text, p.created, u.username, u.avatar, u.frame, u.role
        FROM posts p JOIN users u ON u.id = p.user_id
        ORDER BY p.id DESC LIMIT 20
    """).fetchall()
    return jsonify(posts=[dict(r) for r in rows])


@bp.post('/api/posts')
@login_required
def create_post():
    data = request.json or {}
    text = (data.get('text') or '').strip()
    if not text:
        return jsonify(error="Текст пуст"), 400

    db = get_db()
    today = datetime.now().strftime("%Y-%m-%d")
    user = db.execute(
        "SELECT daily_points, last_points_date FROM users WHERE id = ?",
        (g.user['id'],),
    ).fetchone()

    daily = user['daily_points'] if user['last_points_date'] == today else 0
    points_to_add = 0
    if daily < DAILY_LIMIT:
        points_to_add = min(10, DAILY_LIMIT - daily)

    db.execute(
        "INSERT INTO posts (user_id, text, created) VALUES (?,?,?)",
        (g.user['id'], text, int(time.time())),
    )
    db.execute(
        "UPDATE users SET points = points + ?, daily_points = ?, last_points_date = ? WHERE id = ?",
        (points_to_add, daily + points_to_add, today, g.user['id']),
    )
    db.commit()

    new_total = db.execute(
        "SELECT points FROM users WHERE id = ?", (g.user['id'],)
    ).fetchone()['points']

    return jsonify(
        ok=True,
        points_added=points_to_add,
        new_total=new_total,
        daily_used=daily + points_to_add,
        daily_limit=DAILY_LIMIT,
    )