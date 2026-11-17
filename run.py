from app import create_app
from app.config import Config

app = create_app()

if __name__ == '__main__':
    print(f"🚀 Сервер запущен на http://localhost:{Config.PORT}")
    # Используем встроенный сервер Flask, так как он лучше работает с WebSocket при разработке
    app.run(host='0.0.0.0', port=Config.PORT, debug=True)
from app import create_app

app = create_app()

if __name__ == '__main__':
    app.run(host='127.0.0.1', port=5000, debug=True)