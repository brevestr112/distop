import json
import time
from flask import session, request
from flask_sock import Sock
from .db import get_db

sock = Sock()
clients = {}  # username -> websocket


def _current_user():
    uid = session.get('uid')
    if not uid:
        return None
    return get_db().execute("SELECT id, username FROM users WHERE id = ?", (uid,)).fetchone()


def init_ws(app):
    sock.init_app(app)

    @sock.route('/ws/chat')
    def chat_ws(ws):
        user = _current_user()
        if not user:
            ws.close()
            return

        username = user['username']
        clients[username] = ws

        try:
            while True:
                raw = ws.receive()
                if raw is None:
                    break
                try:
                    data = json.loads(raw)
                except Exception:
                    continue

                to = (data.get('to') or '').strip()
                text = (data.get('text') or '').strip()
                if not to or not text:
                    continue

                db = get_db()
                recipient = db.execute(
                    "SELECT id FROM users WHERE username = ?", (to,)
                ).fetchone()
                if not recipient:
                    continue

                db.execute(
                    "INSERT INTO messages (sender_id, recipient_id, text, created) VALUES (?,?,?,?)",
                    (user['id'], recipient['id'], text, int(time.time())),
                )
                db.commit()

                payload = json.dumps({"from": username, "to": to, "text": text})

                target = clients.get(to)
                if target:
                    try:
                        target.send(payload)
                    except Exception:
                        clients.pop(to, None)

                try:
                    ws.send(payload)
                except Exception:
                    break
        finally:
            clients.pop(username, None)