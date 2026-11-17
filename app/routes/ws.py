import json
import time
from flask import session
from ..db import get_db

ONLINE_USERS = {}

def register_ws(sock):
    @sock.route('/ws/chat')
    def chat_ws(ws):
        uid = session.get('uid')
        if not uid:
            ws.close()
            return

        db = get_db()
        user = db.execute("SELECT id, username FROM users WHERE id = ?", (uid,)).fetchone()
        if not user: 
            return

        username = user['username']
        ONLINE_USERS[username] = ws

        try:
            while True:
                raw_data = ws.receive()
                if not raw_data: break
                
                data = json.loads(raw_data)
                to_user = data.get('to')
                text = data.get('text', '').strip()
                
                if not to_user or not text: continue

                recipient = db.execute("SELECT id, username FROM users WHERE username = ?", (to_user,)).fetchone()
                if not recipient: continue

                # Сохраняем сообщение в базу
                db.execute("INSERT INTO messages (sender_id, recipient_id, text, created) VALUES (?, ?, ?, ?)",
                           (user['id'], recipient['id'], text, int(time.time())))
                db.commit()

                # Отправляем собеседнику (если он в сети)
                payload = json.dumps({"from": username, "text": text})
                if to_user in ONLINE_USERS:
                    try: ONLINE_USERS[to_user].send(payload)
                    except: pass
                
                # Отправляем копию себе
                ws.send(payload)
        except Exception:
            pass
        finally:
            if username in ONLINE_USERS: del ONLINE_USERS[username]