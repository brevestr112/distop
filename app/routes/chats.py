import time
from flask import Blueprint, jsonify, g, request
from ..db import get_db
from ..services.security import login_required

bp = Blueprint('chats', __name__)


@bp.get('/api/chats')
@login_required
def chat_list():
    db = get_db()
    rows = db.execute("""
        SELECT
            u.username AS with_user,
            u.avatar AS with_avatar,
            u.frame AS with_frame,
            m.text AS last_text,
            m.created AS last_created,
            m.sender_id AS last_sender_id
        FROM messages m
        JOIN users u ON u.id = CASE
            WHEN m.sender_id = ? THEN m.recipient_id
            ELSE m.sender_id
        END
        WHERE m.sender_id = ? OR m.recipient_id = ?
        ORDER BY m.id DESC
    """, (g.user['id'], g.user['id'], g.user['id'])).fetchall()

    seen = set()
    result = []
    for r in rows:
        if r['with_user'] in seen:
            continue
        seen.add(r['with_user'])
        result.append({
            "with_user": r['with_user'],
            "avatar": r['with_avatar'],
            "frame": r['with_frame'],
            "last_text": r['last_text'],
            "last_created": r['last_created'],
            "is_mine": r['last_sender_id'] == g.user['id'],
        })
    return jsonify(chats=result)


@bp.get('/api/chats/<username>')
@login_required
def history(username):
    db = get_db()
    other = db.execute("SELECT id, username FROM users WHERE username = ?", (username,)).fetchone()
    if not other:
        return jsonify(error="Пользователь не найден"), 404

    rows = db.execute("""
        SELECT s.username AS sender, m.text, m.created
        FROM messages m
        JOIN users s ON s.id = m.sender_id
        WHERE (m.sender_id = ? AND m.recipient_id = ?)
           OR (m.sender_id = ? AND m.recipient_id = ?)
        ORDER BY m.id ASC LIMIT 200
    """, (g.user['id'], other['id'], other['id'], g.user['id'])).fetchall()

    return jsonify(messages=[dict(r) for r in rows])


# === НОВОЕ: Long Polling ===
@bp.post('/api/chats/send')
@login_required
def send_message():
    data = request.json or {}
    to = (data.get('to') or '').strip()
    text = (data.get('text') or '').strip()
    if not to or not text:
        return jsonify(error="Пустое сообщение"), 400

    db = get_db()
    recipient = db.execute("SELECT id FROM users WHERE username = ?", (to,)).fetchone()
    if not recipient:
        return jsonify(error="Пользователь не найден"), 404

    db.execute(
        "INSERT INTO messages (sender_id, recipient_id, text, created) VALUES (?,?,?,?)",
        (g.user['id'], recipient['id'], text, int(time.time())),
    )
    db.commit()
    return jsonify(ok=True)


@bp.get('/api/chats/poll')
@login_required
def poll_messages():
    """Ждем новых сообщений до 25 секунд (Long Polling)."""
    last_id = int(request.args.get('last_id', 0))
    db = get_db()
    
    start_time = time.time()
    while time.time() - start_time < 25:
        # Ищем новые сообщения для текущего пользователя
        rows = db.execute("""
            SELECT m.id, s.username AS sender, m.text
            FROM messages m
            JOIN users s ON s.id = m.sender_id
            WHERE m.recipient_id = ? AND m.id > ?
            ORDER BY m.id ASC
        """, (g.user['id'], last_id)).fetchall()

        if rows:
            return jsonify(messages=[dict(r) for r in rows])
        
        time.sleep(1)  # Спим секунду и проверяем снова
        
    return jsonify(messages=[])  # Если за 25 сек ничего нет, возвращаем пустой список