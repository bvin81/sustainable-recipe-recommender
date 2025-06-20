#!/usr/bin/env python3
import os
import sys
from pathlib import Path
from flask import Flask

# Project root hozzáadása
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "user_study"))

# Flask app objektum létrehozása (Gunicorn számára)
app = Flask(__name__)

def create_app():
    """Flask alkalmazás factory"""
    app_mode = os.environ.get('APP_MODE', 'user_study')
    
    if app_mode == 'user_study':
        try:
            # Próbáljuk betölteni a user study rendszert
            sys.path.append(str(project_root / "user_study"))
            import user_study
            return user_study.app
        except ImportError as e:
            print(f"❌ User study import error: {e}")
            # Fallback app létrehozása
            return create_fallback_app()
        except Exception as e:
            print(f"❌ User study error: {e}")
            return create_fallback_app()
    else:
        return create_fallback_app()

def create_fallback_app():
    """Egyszerű fallback alkalmazás"""
    fallback_app = Flask(__name__)
    
    @fallback_app.route('/')
    def home():
        return '''
        <!DOCTYPE html>
        <html lang="hu">
        <head>
            <meta charset="UTF-8">
            <title>Sustainable Recipe Recommender</title>
            <style>
                body {
                    font-family: Arial, sans-serif;
                    max-width: 800px;
                    margin: 0 auto;
                    padding: 40px 20px;
                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                    min-height: 100vh;
                    color: white;
                    text-align: center;
                }
                .container {
                    background: white;
                    color: #333;
                    padding: 40px;
                    border-radius: 15px;
                    box-shadow: 0 10px 30px rgba(0,0,0,0.3);
                }
                .logo { font-size: 3em; margin-bottom: 20px; }
                .status { background: #fff3cd; padding: 20px; border-radius: 10px; margin: 20px 0; }
            </style>
        </head>
        <body>
            <div class="container">
                <div class="logo">🌱🍽️</div>
                <h1>Sustainable Recipe Recommender</h1>
                <div class="status">
                    <h3>🔧 Rendszer Állapot</h3>
                    <p>✅ Flask App: Működik</p>
                    <p>✅ Heroku Deploy: Sikeres</p>
                    <p>🔄 User Study: Fejlesztés alatt</p>
                    <p><strong>Következő lépés:</strong> User study fájlok telepítése</p>
                </div>
                <p>📊 Dataset: 100 rețetá előkészítve</p>
                <p>🎯 A/B/C Testing: Készen áll</p>
            </div>
        </body>
        </html>
        '''
    
    @fallback_app.route('/health')
    def health():
        return {'status': 'OK', 'message': 'App is running'}
    
    return fallback_app

# App inicializálás
try:
    app = create_app()
    print("✅ App successfully created")
except Exception as e:
    print(f"❌ App creation failed: {e}")
    app = create_fallback_app()

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
