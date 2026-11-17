import threading
import time
import webview
from app import create_app
from app.config import Config

def start_server():
    # Запускаем Flask-сервер в фоне
    app = create_app()
    app.run(host='127.0.0.1', port=Config.PORT, threaded=True)

def main():
    # 1. Запускаем сервер в отдельном потоке
    server_thread = threading.Thread(target=start_server, daemon=True)
    server_thread.start()

    # 2. Ждем пару секунд, чтобы сервер успел подняться
    time.sleep(2)

    # 3. Открываем нативное окно приложения
    webview.create_window(
        title="Distop", 
        url=f"http://127.0.0.1:{Config.PORT}", 
        width=1200, 
        height=800,
        min_size=(800, 600)
    )
    
    # Запускаем цикл приложения
    webview.start()

if __name__ == '__main__':
    main()