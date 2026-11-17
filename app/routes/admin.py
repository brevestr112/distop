import time
from flask import Blueprint, jsonify, g, request
from ..db import get_db
from ..services.security import login_required

bp = Blueprint('admin', __name__)

ROLE_RANK = {'user': 0, 'moderator': 1, 'ceo': 2, 'creator': 3}


def _rank(role):
    return ROLE_RANK.get(role, 0)


def _log(db, action, target='', details=''):
    db.execute(
        "INSERT INTO admin_log (admin_id, action, target, details, created) VALUES (?,?,?,?,?)",
        (g.user['id'], action, target, details, int(time.time())),
    )


@bp.get('/api/admin/users')
@login_required
def admin_users():
    if _rank(g.user['role']) < 1:
        return jsonify(error="Доступ запрещен"), 403
    q = (request.args.get('q') or '').strip()
    db = get_db()
    sql = ("SELECT id, username, role, points, banned, ban_reason, frame, avatar, created "
           "FROM users")
    args = ()
    if q:
        sql += " WHERE username LIKE ?"
        args = (f'%{q}%',)
    sql += " ORDER BY id"
    users = db.execute(sql, args).fetchall()
    return jsonify(users=[dict(u) for u in users])


@bp.get('/api/admin/stats')
@login_required
def admin_stats():
    if _rank(g.user['role']) < 1:
        return jsonify(error="Доступ запрещен"), 403
    db = get_db()
    stats = {
        "users": db.execute("SELECT COUNT(*) c FROM users").fetchone()['c'],
        "banned": db.execute("SELECT COUNT(*) c FROM users WHERE banned = 1").fetchone()['c'],
        "posts": db.execute("SELECT COUNT(*) c FROM posts").fetchone()['c'],
        "messages": db.execute("SELECT COUNT(*) c FROM messages").fetchone()['c'],
        "reports_open": db.execute("SELECT COUNT(*) c FROM reports WHERE status='open'").fetchone()['c'],
    }
    return jsonify(stats=stats)


@bp.post('/api/admin/role')
@login_required
def set_role():
    me = g.user['role']
    if _rank(me) < 2:
        return jsonify(error="Только CEO и Создатель меняют роли"), 403
    data = request.json or {}
    target = data.get('username')
    new_role = data.get('role')
    if new_role not in ROLE_RANK:
        return jsonify(error="Неизвестная роль"), 400
    if _rank(new_role) > _rank(me):
        return jsonify(error="Нельзя выдать роль выше своей"), 403

    db = get_db()
    victim = db.execute("SELECT role FROM users WHERE username = ?", (target,)).fetchone()
    if not victim:
        return jsonify(error="Пользователь не найден"), 404
    if victim['role'] == 'creator' and me != 'creator':
        return jsonify(error="Создателя может менять только создатель"), 403

    db.execute("UPDATE users SET role = ? WHERE username = ?", (new_role, target))
    _log(db, "set_role", target, f"{victim['role']} -> {new_role}")
    db.commit()
    return jsonify(ok=True)


@bp.post('/api/admin/ban')
@login_required
def ban_user():
    if _rank(g.user['role']) < 1:
        return jsonify(error="Доступ запрещен"), 403
    data = request.json or {}
    target = data.get('username')
    reason = (data.get('reason') or 'нарушение правил')[:200]
    db = get_db()
    victim = db.execute("SELECT role, banned FROM users WHERE username = ?", (target,)).fetchone()
    if not victim:
        return jsonify(error="Пользователь не найден"), 404
    if _rank(victim['role']) >= _rank(g.user['role']) and g.user['role'] != 'creator':
        return jsonify(error="Нельзя банить равного или старше"), 403
    db.execute("UPDATE users SET banned = 1, ban_reason = ? WHERE username = ?", (reason, target))
    _log(db, "ban", target, reason)
    db.commit()
    return jsonify(ok=True)


@bp.post('/api/admin/unban')
@login_required
def unban_user():
    if _rank(g.user['role']) < 1:
        return jsonify(error="Доступ запрещен"), 403
    data = request.json or {}
    target = data.get('username')
    db = get_db()
    db.execute("UPDATE users SET banned = 0, ban_reason = '' WHERE username = ?", (target,))
    _log(db, "unban", target)
    db.commit()
    return jsonify(ok=True)


@bp.post('/api/admin/points')
@login_required
def change_points():
    if _rank(g.user['role']) < 2:
        return jsonify(error="Только CEO и Создатель меняют баллы"), 403
    data = request.json or {}
    target = data.get('username')
    delta = int(data.get('delta') or 0)
    db = get_db()
    victim = db.execute("SELECT points FROM users WHERE username = ?", (target,)).fetchone()
    if not victim:
        return jsonify(error="Пользователь не найден"), 404
    new_val = max(0, victim['points'] + delta)
    db.execute("UPDATE users SET points = ? WHERE username = ?", (new_val, target))
    _log(db, "points", target, f"{delta:+d} -> {new_val}")
    db.commit()
    return jsonify(ok=True, points=new_val)


@bp.post('/api/admin/delete_user')
@login_required
def delete_user():
    if _rank(g.user['role']) < 2:
        return jsonify(error="Только CEO и Создатель удаляют пользователей"), 403
    data = request.json or {}
    target = data.get('username')
    if target == g.user['username']:
        return jsonify(error="Нельзя удалить себя"), 400
    db = get_db()
    victim = db.execute("SELECT id, role FROM users WHERE username = ?", (target,)).fetchone()
    if not victim:
        return jsonify(error="Пользователь не найден"), 404
    if victim['role'] == 'creator' and g.user['role'] != 'creator':
        return jsonify(error="Создателя может удалить только создатель"), 403
    uid = victim['id']
    db.execute("DELETE FROM messages WHERE sender_id = ? OR recipient_id = ?", (uid, uid))
    db.execute("DELETE FROM posts WHERE user_id = ?", (uid,))
    db.execute("DELETE FROM purchases WHERE user_id = ?", (uid,))
    db.execute("DELETE FROM friends WHERE user_id = ? OR friend_id = ?", (uid, uid))
    db.execute("DELETE FROM users WHERE id = ?", (uid,))
    _log(db, "delete_user", target)
    db.commit()
    return jsonify(ok=True)


@bp.post('/api/admin/delete_post')
@login_required
def delete_post():
    if _rank(g.user['role']) < 1:
        return jsonify(error="Доступ запрещен"), 403
    data = request.json or {}
    pid = int(data.get('post_id') or 0)
    db = get_db()
    db.execute("DELETE FROM posts WHERE id = ?", (pid,))
    _log(db, "delete_post", str(pid))
    db.commit()
    return jsonify(ok=True)


@bp.get('/api/admin/log')
@login_required
def admin_log():
    if _rank(g.user['role']) < 1:
        return jsonify(error="Доступ запрещен"), 403
    db = get_db()
    rows = db.execute("""
        SELECT a.id, a.action, a.target, a.details, a.created, u.username AS admin
        FROM admin_log a JOIN users u ON u.id = a.admin_id
        ORDER BY a.id DESC LIMIT 100
    """).fetchall()
    return jsonify(log=[dict(r) for r in rows])