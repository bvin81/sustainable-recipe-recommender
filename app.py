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
            print(f"❌ Error: {e}")
            print("User study files will be added later!")
            sys.exit(1)
    else:
        print(f"❌ Unknown APP_MODE: {app_mode}")
        sys.exit(1)

if __name__ == '__main__':
    main()
