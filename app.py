#!/usr/bin/env python3
import os
import sys
from pathlib import Path

# Project root hozzáadása
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "user_study"))

def main():
    app_mode = os.environ.get('APP_MODE', 'user_study')
    
    if app_mode == 'user_study':
        try:
            from user_study.user_study import app
            port = int(os.environ.get('PORT', 5000))
            debug = os.environ.get('FLASK_ENV') != 'production'
            print(f"🔬 Starting User Study System on port {port}")
            app.run(host='0.0.0.0', port=port, debug=debug)
        except ImportError as e:
            print(f"❌ Error importing user_study: {e}")
            # Fallback to basic app
            from flask import Flask
            fallback_app = Flask(__name__)
            
            @fallback_app.route('/')
            def fallback():
                return f'''
                <div style="text-align: center; padding: 40px; font-family: Arial;">
                    <h1>🚧 User Study System</h1>
                    <p>❌ Import Error: {e}</p>
                    <p>🔧 Hiányzó fájlok pótlása szükséges</p>
                    <p><strong>Következő lépés:</strong> user_study fájlok hozzáadása</p>
                </div>
                '''
            
            port = int(os.environ.get('PORT', 5000))
            fallback_app.run(host='0.0.0.0', port=port, debug=False)
    else:
        print(f"❌ Unknown APP_MODE: {app_mode}")
        sys.exit(1)

if __name__ == '__main__':
    main()
