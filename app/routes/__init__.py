from . import auth, posts, shop, admin, chats


def register_routes(app):
    app.register_blueprint(auth.bp)
    app.register_blueprint(posts.bp)
    app.register_blueprint(shop.bp)
    app.register_blueprint(admin.bp)
    app.register_blueprint(chats.bp)