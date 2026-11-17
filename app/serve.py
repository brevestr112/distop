from waitress import serve
from app import create_app

app = create_app()

if __name__ == '__main__':
    print("Сервер запущен! Открой http://127.0.0.1:5000")
    serve(app, host='0.0.0.0', port=5000, threads=50)