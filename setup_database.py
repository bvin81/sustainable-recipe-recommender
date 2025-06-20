#!/usr/bin/env python3
"""
GYORS FIX - setup_database.py
Javítja a deployment problémákat
"""

import os
import sys
import sqlite3
from pathlib import Path
import pandas as pd

def test_database():
    """Adatbázis tesztelése"""
    print("🔧 Adatbázis tesztelése...")
    
    try:
        conn = sqlite3.connect('user_study.db')
        
        # Táblák ellenőrzése
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['participants', 'interactions', 'questionnaire']
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            print(f"❌ Hiányzó táblák: {missing_tables}")
            return False
        
        # Test insert
        cursor.execute('''
            INSERT INTO participants 
            (age_group, education, cooking_frequency, sustainability_awareness, version)
            VALUES (?, ?, ?, ?, ?)
        ''', ('25-34', 'bachelor', 'weekly', 3, 'v1'))
        
        user_id = cursor.lastrowid
        conn.commit()
        
        # Test query
        cursor.execute('SELECT COUNT(*) FROM participants')
        count = cursor.fetchone()[0]
        
        conn.close()
        
        print(f"✅ Adatbázis teszt sikeres (user_id: {user_id}, count: {count})")
        return True
        
    except Exception as e:
        print(f"❌ Adatbázis teszt hiba: {e}")
        return False

def main():
    """Fő setup script"""
    print("🚀 GYORS FIX SETUP")
    print("=" * 30)
    
    success = True
    
    # 1. Könyvtárak
    success &= create_directories()
    
    # 2. Sample receptek
    success &= create_sample_recipes()
    
    # 3. Adatbázis séma javítása
    success &= fix_database_schema()
    
    # 4. Adatbázis tesztelése
    success &= test_database()
    
    print("\n" + "=" * 30)
    if success:
        print("🎉 SETUP SIKERES!")
        print("\n📋 ELLENŐRZÉS:")
        print(f"✅ Data könyvtár: {os.path.exists('data')}")
        print(f"✅ Processed recipes: {os.path.exists('data/processed_recipes.csv')}")
        print(f"✅ Database: {os.path.exists('user_study.db')}")
        
        # CSV tartalom ellenőrzése
        if os.path.exists('data/processed_recipes.csv'):
            df = pd.read_csv('data/processed_recipes.csv')
            print(f"✅ Receptek száma: {len(df)}")
            print(f"✅ Oszlopok: {list(df.columns)}")
        
        print("\n🚀 KÖVETKEZŐ LÉPÉSEK:")
        print("1. Git commit és push a javításokkal")
        print("2. Heroku automatikusan redeploy-ol")
        print("3. Tesztelje a regisztrációt")
        
    else:
        print("❌ SETUP SIKERTELEN!")
        print("Ellenőrizze a hibákat és próbálja újra.")
    
    return success

if __name__ == "__main__":
    main() create_sample_recipes():
    """Gyors sample receptek létrehozása"""
    print("🔧 Sample receptek létrehozása...")
    
    # Magyar receptek
    recipes_data = [
        {
            'recipeid': 1,
            'title': 'Hagyományos Gulyásleves',
            'ingredients': 'marhahús, hagyma, paprika, paradicsom, burgonya, fokhagyma, kömény, majoranna',
            'instructions': '1. A húst kockákra vágjuk és enyhén megsózzuk. 2. Megdinszteljük a hagymát, hozzáadjuk a paprikát. 3. Felöntjük vízzel és főzzük 1.5 órát. 4. Hozzáadjuk a burgonyát és tovább főzzük.',
            'images': '',
            'HSI': 75.0, 'ESI': 60.0, 'PPI': 90.0, 'composite_score': 71.0
        },
        {
            'recipeid': 2,
            'title': 'Vegetáriánus Lecsó',
            'ingredients': 'paprika, paradicsom, hagyma, tojás, kolbász helyett tofu, olívaolaj, só, bors, fokhagyma',
            'instructions': '1. A hagymát és fokhagymát megdinszteljük olívaolajban. 2. Hozzáadjuk a felszeletelt paprikát. 3. Paradicsomot és kockára vágott tofut adunk hozzá. 4. Tojással dúsítjuk.',
            'images': '',
            'HSI': 85.0, 'ESI': 90.0, 'PPI': 70.0, 'composite_score': 83.0
        },
        {
            'recipeid': 3,
            'title': 'Rántott Schnitzel Burgonyával',
            'ingredients': 'sertéshús, liszt, tojás, zsemlemorzsa, burgonya, olaj, só, bors',
            'instructions': '1. A húst kikalapáljuk és megsózzuk. 2. Lisztbe, majd felvert tojásba, végül zsemlemorzsába forgatjuk. 3. Forró olajban mindkét oldalán kisütjük. 4. A burgonyát héjában megfőzzük.',
            'images': '',
            'HSI': 55.0, 'ESI': 45.0, 'PPI': 85.0, 'composite_score': 57.0
        },
        {
            'recipeid': 4,
            'title': 'Halászlé Szegedi Módra',
            'ingredients': 'ponty, csuka, harcsa, hagyma, paradicsom, paprika, só, babérlevél',
            'instructions': '1. A halakat megtisztítjuk és feldaraboljuk. 2. A halak fejéből és farkából erős alapot főzünk. 3. Az alapot leszűrjük és beletesszük a haldarabokat. 4. Paprikával ízesítjük.',
            'images': '',
            'HSI': 80.0, 'ESI': 70.0, 'PPI': 75.0, 'composite_score': 74.0
        },
        {
            'recipeid': 5,
            'title': 'Gombapaprikás Galuskával',
            'ingredients': 'gomba, hagyma, paprika, tejföl, liszt, tojás, petrezselyem, olaj',
            'instructions': '1. A gombát felszeleteljük és kisütjük. 2. Hagymát dinsztelünk, paprikát adunk hozzá. 3. A gombát hozzáadjuk, tejföllel lefuttatjuk. 4. Galuskát főzünk mellé.',
            'images': '',
            'HSI': 70.0, 'ESI': 75.0, 'PPI': 65.0, 'composite_score': 71.5
        }
    ]
    
    # Data könyvtár létrehozása
    os.makedirs('data', exist_ok=True)
    
    # CSV mentése
    df = pd.DataFrame(recipes_data)
    df.to_csv('data/processed_recipes.csv', index=False, encoding='utf-8')
    
    print(f"✅ {len(recipes_data)} recept létrehozva: data/processed_recipes.csv")
    return True

def fix_database_schema():
    """Adatbázis séma javítása"""
    print("🔧 Adatbázis séma javítása...")
    
    # SQLite adatbázis létrehozása
    conn = sqlite3.connect('user_study.db')
    
    # Táblák törlése ha léteznek
    conn.execute('DROP TABLE IF EXISTS interactions')
    conn.execute('DROP TABLE IF EXISTS questionnaire') 
    conn.execute('DROP TABLE IF EXISTS participants')
    conn.execute('DROP TABLE IF EXISTS users')  # Régi tábla
    
    # JAVÍTOTT participants tábla
    conn.execute('''
        CREATE TABLE participants (
            user_id INTEGER PRIMARY KEY AUTOINCREMENT,
            age_group TEXT NOT NULL,
            education TEXT NOT NULL,
            cooking_frequency TEXT NOT NULL,
            sustainability_awareness INTEGER NOT NULL,
            consent_participation BOOLEAN NOT NULL DEFAULT 1,
            consent_data BOOLEAN NOT NULL DEFAULT 1,
            consent_publication BOOLEAN NOT NULL DEFAULT 1,
            consent_contact BOOLEAN DEFAULT 0,
            version TEXT NOT NULL,
            is_completed BOOLEAN DEFAULT 0,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Interactions tábla
    conn.execute('''
        CREATE TABLE interactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            recipe_id INTEGER,
            rating INTEGER,
            explanation_helpful INTEGER,
            view_time_seconds REAL,
            interaction_order INTEGER,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES participants (user_id)
        )
    ''')
    
    # Questionnaire tábla
    conn.execute('''
        CREATE TABLE questionnaire (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            system_usability INTEGER,
            recommendation_quality INTEGER,
            trust_level INTEGER,
            explanation_clarity INTEGER,
            sustainability_importance INTEGER,
            overall_satisfaction INTEGER,
            additional_comments TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES participants (user_id)
        )
    ''')
    
    conn.commit()
    conn.close()
    
    print("✅ Adatbázis séma javítva")
    return True

def create_directories():
    """Szükséges könyvtárak létrehozása"""
    print("🔧 Könyvtárak létrehozása...")
    
    directories = [
        'data',
        'static',
        'static/images',
        'user_study',
        'user_study/templates',
        'user_study/templates/user_study',
        'results'
    ]
    
    for directory in directories:
        os.makedirs(directory, exist_ok=True)
    
    print("✅ Könyvtárak létrehozva")
    return True

def
