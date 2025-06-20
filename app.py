from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def home():
    return '''
    <!DOCTYPE html>
    <html lang="hu">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
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
            .btn {
                background: linear-gradient(45deg, #27ae60, #2ecc71);
                color: white;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 25px;
                font-size: 1.1em;
                font-weight: bold;
                display: inline-block;
                margin: 10px;
            }
        </style>
    </head>
    <body>
        <div class="container">
            <div class="logo">🌱🍽️</div>
            <h1>Sustainable Recipe Recommender</h1>
            <p>✅ App sikeresen telepítve!</p>
            <p>🔧 Rendszer alatt fejlesztés...</p>
            <a href="/test" class="btn">🧪 Teszt Oldal</a>
            <a href="/status" class="btn">📊 Státusz</a>
        </div>
    </body>
    </html>
    '''

@app.route('/test')
def test():
    return '''
    <div style="text-align: center; padding: 40px; font-family: Arial;">
        <h2>✅ Teszt Oldal Működik!</h2>
        <p>🎉 Flask alkalmazás sikeresen fut!</p>
        <a href="/" style="color: #27ae60;">← Vissza a főoldalra</a>
    </div>
    '''

@app.route('/status')
def status():
    return '''
    <div style="text-align: center; padding: 40px; font-family: Arial;">
        <h2>📊 Alkalmazás Státusz</h2>
        <p>✅ Flask: Működik</p>
        <p>✅ Heroku: Deployed</p>
        <p>🔄 User Study: Fejlesztés alatt</p>
        <a href="/" style="color: #27ae60;">← Vissza a főoldalra</a>
    </div>
    '''

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=False)
