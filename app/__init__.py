import os
from flask import Flask, render_template
from .db import init_db, close_db
from .routes import register_routes

def create_app():
    app = Flask(__name__, template_folder='templates')

    base = os.path.abspath(os.path.dirname(os.path.dirname(__file__)))
    data_dir = os.path.join(base, 'data')
    os.makedirs(data_dir, exist_ok=True)

    app.config['DB_PATH'] = os.path.join(data_dir, 'distop.db')
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-change-me')

    app.teardown_appcontext(close_db)
    init_db(app)
    register_routes(app)

    @app.route('/')
    def index():
        return render_template('index.html')

    return app