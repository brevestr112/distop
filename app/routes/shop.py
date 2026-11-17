from flask import Blueprint, jsonify, g
from ..db import get_db
from ..services.security import login_required
import time

bp = Blueprint('shop', __name__)

@bp.get('/api/shop')
@login_required
def get_shop():
    db = get_db()
    items = db.execute("SELECT * FROM shop_items").fetchall()
    bought = [r['item_id'] for r in db.execute("SELECT item_id FROM purchases WHERE user_id = ?", (g.user['id'],)).fetchall()]
    return jsonify(items=[{**dict(i), "bought": i['id'] in bought} for i in items])

@bp.post('/api/shop/buy/<int:item_id>')
@login_required
def buy(item_id):
    db = get_db()
    item = db.execute("SELECT * FROM shop_items WHERE id = ?", (item_id,)).fetchone()
    
    if not item: return jsonify(error="Нет товара"), 404
    if g.user['points'] < item['price']: return jsonify(error="Мало баллов"), 400
    if db.execute("SELECT 1 FROM purchases WHERE user_id = ? AND item_id = ?", (g.user['id'], item_id)).fetchone():
        return jsonify(error="Уже куплено"), 400

    db.execute("UPDATE users SET points = points - ? WHERE id = ?", (item['price'], g.user['id']))
    db.execute("INSERT INTO purchases (user_id, item_id, created) VALUES (?, ?, ?)", (g.user['id'], item_id, int(time.time())))
    
    # Применение купленного
    if item['type'] == 'frame': db.execute("UPDATE users SET frame = ? WHERE id = ?", (item['css_class'], g.user['id']))
    elif item['type'] == 'chat_theme': db.execute("UPDATE users SET chat_theme = ? WHERE id = ?", (item['css_class'], g.user['id']))
    elif item['type'] == 'nick_color': db.execute("UPDATE users SET nick_color = ? WHERE id = ?", (item['css_class'], g.user['id']))
    elif item['type'] == 'avatar_effect': db.execute("UPDATE users SET avatar_effect = ? WHERE id = ?", (item['css_class'], g.user['id']))
    elif item['type'] == 'font_style': db.execute("UPDATE users SET font_style = ? WHERE id = ?", (item['css_class'], g.user['id']))
    elif item['type'] == 'bg_effect': db.execute("UPDATE users SET bg_effect = ? WHERE id = ?", (item['css_class'], g.user['id']))
    elif item['type'] == 'banner_effect': db.execute("UPDATE users SET banner_effect = ? WHERE id = ?", (item['css_class'], g.user['id']))
        
    db.commit()
    return jsonify(ok=True)