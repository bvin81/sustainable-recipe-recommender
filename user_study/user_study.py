#!/usr/bin/env python3
"""
Enhanced User Study System - Valós Magyar Receptekkel
Verzió információ elrejtése, teljesítmény tracking, képek
"""

import os
import sys
import sqlite3
import datetime
import random
import hashlib
import pandas as pd
import numpy as np
from pathlib import Path
from flask import Blueprint, render_template, request, session, redirect, url_for, jsonify, g

# Project path setup
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Blueprint létrehozása - FONTOS!
user_study_bp = Blueprint('user_study', __name__, url_prefix='')

class DatabaseManager:
    """Adatbázis kezelő osztály"""
    
    def __init__(self, db_path="user_study.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Adatbázis kapcsolat létrehozása"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """Adatbázis táblák inicializálása"""
        conn = self.get_connection()
        
        # Felhasználók tábla
        conn.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                age_group TEXT NOT NULL,
                cooking_experience TEXT NOT NULL,
                dietary_restrictions TEXT,
                sustainability_awareness INTEGER,
                version TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Interakciók tábla
        conn.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                action TEXT NOT NULL,
                recipe_id INTEGER,
                rating INTEGER,
                explanation_helpful BOOLEAN,
                view_time_seconds REAL,
                interaction_order INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                version TEXT,
                data TEXT,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Kérdőív válaszok tábla  
        conn.execute('''
            CREATE TABLE IF NOT EXISTS questionnaire_responses (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                question_key TEXT NOT NULL,
                response TEXT NOT NULL,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES users (id)
            )
        ''')
        
        # Recept teljesítmény tábla
        conn.execute('''
            CREATE TABLE IF NOT EXISTS recipe_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                version TEXT NOT NULL,
                total_views INTEGER DEFAULT 0,
                total_ratings INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0,
                total_positive_ratings INTEGER DEFAULT 0,
                last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def log_interaction(self, user_id, action, recipe_id=None, rating=None, 
                       explanation_helpful=None, view_time=None, 
                       interaction_order=None, data=None):
        """Felhasználói interakció naplózása"""
        conn = self.get_connection()
        version = self.get_user_version(user_id)
        
        conn.execute('''
            INSERT INTO interactions 
            (user_id, action, recipe_id, rating, explanation_helpful, 
             view_time_seconds, interaction_order, version, data)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (user_id, action, recipe_id, rating, explanation_helpful, 
              view_time, interaction_order, version, str(data) if data else None))
        
        conn.commit()
        conn.close()
    
    def get_user_version(self, user_id):
        """Felhasználó verziójának lekérése"""
        conn = self.get_connection()
        result = conn.execute('SELECT version FROM users WHERE id = ?', (user_id,)).fetchone()
        conn.close()
        return result['version'] if result else None

class EnhancedRecipeRecommender:
    """Továbbfejlesztett recept ajánló rendszer valós magyar receptekkel"""
    
    def __init__(self):
        self.recipes_df = self.load_hungarian_recipes()
        self.performance_tracker = {}
    
    def load_hungarian_recipes(self) -> pd.DataFrame:
        """Magyar receptek betöltése"""
        try:
            csv_path = project_root / "data" / "processed_recipes.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                print(f"✅ Betöltve {len(df)} magyar recept")
                return df
            else:
                print("⚠️ processed_recipes.csv nem található, sample adatok használata")
                return self.create_hungarian_sample()
        except Exception as e:
            print(f"Recept betöltési hiba: {e}")
            return self.create_hungarian_sample()
    
    def create_hungarian_sample(self) -> pd.DataFrame:
        """Magyar minta receptek létrehozása"""
        hungarian_recipes = [
            {
                'recipeid': 1,
                'title': 'Hagyományos Gulyásleves',
                'ingredients': 'marhahús, hagyma, paprika, paradicsom, burgonya, fokhagyma, kömény, majoranna',
                'instructions': '1. A húst kockákra vágjuk 2. Megdinszteljük a hagymát 3. Hozzáadjuk a paprikát 4. Felöntjük vízzel és főzzük 1.5 órát',
                'images': '/static/images/gulyas.jpg',
                'HSI': 75.0, 'ESI': 60.0, 'PPI': 90.0, 'composite_score': 71.0
            },
            {
                'recipeid': 2,
                'title': 'Rántott Schnitzel Burgonyával',
                'ingredients': 'sertéshús, liszt, tojás, zsemlemorzsa, burgonya, olaj, só, bors',
                'instructions': '1. A húst kikalapáljuk 2. Lisztbe, tojásba, morzsába forgatjuk 3. Forró olajban kisütjük',
                'images': '/static/images/schnitzel.jpg',
                'HSI': 55.0, 'ESI': 45.0, 'PPI': 85.0, 'composite_score': 57.0
            },
            {
                'recipeid': 3,
                'title': 'Vegetáriánus Lecsó',
                'ingredients': 'paprika, paradicsom, hagyma, tojás, kolbász helyett tofu, olívaolaj, só, bors',
                'instructions': '1. A hagymát megdinszteljük 2. Hozzáadjuk a paprikát 3. Paradicsomot és tofut adunk hozzá',
                'images': '/static/images/lecso.jpg',
                'HSI': 85.0, 'ESI': 90.0, 'PPI': 70.0, 'composite_score': 83.0
            },
            {
                'recipeid': 4,
                'title': 'Halászlé Szegedi Módra',
                'ingredients': 'ponty, csuka, hagyma, paradicsom, paprika, só, bors',
                'instructions': '1. A halakat feldaraboljuk 2. Erős tűzön főzzük a halléből 3. Paprikával ízesítjük',
                'images': '/static/images/halaszle.jpg',
                'HSI': 80.0, 'ESI': 70.0, 'PPI': 75.0, 'composite_score': 74.0
            },
            {
                'recipeid': 5,
                'title': 'Töltött Káposzta',
                'ingredients': 'savanyú káposzta, darált hús, rizs, hagyma, paprika, kolbász, tejföl',
                'instructions': '1. A káposztaleveleket leforrázuk 2. Megtöltjük a húsos rizzsel 3. Rétegesen főzzük',
                'images': '/static/images/toltott_kaposzta.jpg',
                'HSI': 70.0, 'ESI': 55.0, 'PPI': 88.0, 'composite_score': 67.6
            }
        ]
        
        return pd.DataFrame(hungarian_recipes)
    
    def get_recommendations_v1(self, user_preferences, user_id):
        """V1: Alaprendszer - ingrediens alapú hasonlóság"""
        # Egyszerű véletlenszerű kiválasztás az adatokból
        sample_size = min(5, len(self.recipes_df))
        recommendations = self.recipes_df.sample(n=sample_size).to_dict('records')
        
        # Performance tracking
        for rec in recommendations:
            self.track_view(rec['recipeid'], 'v1')
        
        return recommendations
    
    def get_recommendations_v2(self, user_preferences, user_id):
        """V2: Hibrid rendszer - egészség és környezeti tényezőkkel"""
        # Kompozit score alapú rendezés
        sorted_recipes = self.recipes_df.sort_values('composite_score', ascending=False)
        recommendations = sorted_recipes.head(5).to_dict('records')
        
        # Performance tracking
        for rec in recommendations:
            self.track_view(rec['recipeid'], 'v2')
        
        return recommendations
    
    def get_recommendations_v3(self, user_preferences, user_id):
        """V3: Magyarázó rendszer - részletes indoklásokkal"""
        # Kompozit score + magyarázatok
        sorted_recipes = self.recipes_df.sort_values('composite_score', ascending=False)
        recommendations = sorted_recipes.head(5).to_dict('records')
        
        # Magyarázatok hozzáadása
        for rec in recommendations:
            rec['explanation'] = self.generate_explanation(rec)
            self.track_view(rec['recipeid'], 'v3')
        
        return recommendations
    
    def generate_explanation(self, recipe):
        """Magyarázat generálása recepthez"""
        explanations = []
        
        if recipe['HSI'] > 70:
            explanations.append("Magas tápérték és egészséges összetevők")
        if recipe['ESI'] > 70:
            explanations.append("Környezetbarát ingrediensek")
        if recipe['PPI'] > 80:
            explanations.append("Népszerű és kipróbált recept")
        
        if not explanations:
            explanations.append("Kiegyensúlyozott összetevők")
        
        return " • ".join(explanations)
    
    def track_view(self, recipe_id, version):
        """Recept megtekintés követése"""
        key = f"{recipe_id}_{version}"
        if key not in self.performance_tracker:
            self.performance_tracker[key] = {'views': 0, 'ratings': []}
        self.performance_tracker[key]['views'] += 1

# Global objektumok inicializálása
db = DatabaseManager()
recommender = EnhancedRecipeRecommender()

def get_user_version():
    """Felhasználó verziójának meghatározása"""
    if 'version' not in session:
        versions = ['v1', 'v2', 'v3']
        session['version'] = random.choice(versions)
    return session['version']

def update_recipe_performance(recipe_id, rating, version):
    """Recept teljesítmény frissítése"""
    try:
        conn = db.get_connection()
        
        # Jelenlegi adatok lekérése
        current = conn.execute('''
            SELECT * FROM recipe_performance 
            WHERE recipe_id = ? AND version = ?
        ''', (recipe_id, version)).fetchone()
        
        if current:
            # Frissítés
            new_total_ratings = current['total_ratings'] + 1
            new_avg_rating = ((current['avg_rating'] * current['total_ratings']) + rating) / new_total_ratings
            new_positive = current['total_positive_ratings'] + (1 if rating >= 4 else 0)
            
            conn.execute('''
                UPDATE recipe_performance 
                SET total_ratings = ?, avg_rating = ?, total_positive_ratings = ?, 
                    last_updated = CURRENT_TIMESTAMP
                WHERE recipe_id = ? AND version = ?
            ''', (new_total_ratings, new_avg_rating, new_positive, recipe_id, version))
        else:
            # Új rekord
            conn.execute('''
                INSERT INTO recipe_performance 
                (recipe_id, version, total_views, total_ratings, avg_rating, total_positive_ratings)
                VALUES (?, ?, 1, 1, ?, ?)
            ''', (recipe_id, version, rating, 1 if rating >= 4 else 0))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Performance update error: {e}")

# Blueprint Route-ok

@user_study_bp.route('/')
def welcome():
    """Üdvözlő oldal"""
    return render_template('user_study/welcome.html')

@user_study_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Felhasználó regisztráció - VERZIÓ ELREJTÉSE"""
    if request.method == 'POST':
        try:
            # Felhasználói adatok gyűjtése
            age_group = request.form.get('age_group')
            cooking_experience = request.form.get('cooking_experience')
            dietary_restrictions = request.form.get('dietary_restrictions', '')
            sustainability_awareness = int(request.form.get('sustainability_awareness', 3))
            
            # Verzió hozzárendelése (ELREJTVE a felhasználó elől!)
            version = get_user_version()
            
            # Felhasználó mentése adatbázisba
            conn = db.get_connection()
            cursor = conn.execute('''
                INSERT INTO users (age_group, cooking_experience, dietary_restrictions, 
                                 sustainability_awareness, version)
                VALUES (?, ?, ?, ?, ?)
            ''', (age_group, cooking_experience, dietary_restrictions, 
                  sustainability_awareness, version))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Session beállítása
            session['user_id'] = user_id
            session['version'] = version
            session['registration_time'] = datetime.datetime.now().isoformat()
            
            # Regisztráció naplózása
            db.log_interaction(user_id, 'register', data={
                'age_group': age_group,
                'cooking_experience': cooking_experience,
                'sustainability_awareness': sustainability_awareness
            })
            
            return redirect(url_for('user_study.instructions'))
            
        except Exception as e:
            print(f"Registration error: {e}")
            return render_template('user_study/register.html', 
                                 error='Regisztráció sikertelen. Kérjük próbálja újra.')
    
    return render_template('user_study/register.html')

@user_study_bp.route('/instructions')
def instructions():
    """Instrukciók oldal - VERZIÓ ELREJTÉSE"""
    if 'user_id' not in session:
        return redirect(url_for('user_study.register'))
    
    # Verzió információt NEM adjuk át a template-nek
    return render_template('user_study/instructions.html')

@user_study_bp.route('/study')
def study():
    """Fő tanulmány oldal - valós magyar receptekkel"""
    if 'user_id' not in session:
        return redirect(url_for('user_study.register'))
    
    user_id = session['user_id']
    version = get_user_version()
    
    # Session tracking
    if 'study_start_time' not in session:
        session['study_start_time'] = datetime.datetime.now().isoformat()
    
    # Felhasználói preferenciák (később bővíthető)
    user_preferences = {
        'sustainability_awareness': session.get('sustainability_awareness', 3)
    }
    
    # Ajánlások lekérése verzió alapján
    if version == 'v1':
        recommendations = recommender.get_recommendations_v1(user_preferences, user_id)
    elif version == 'v2':
        recommendations = recommender.get_recommendations_v2(user_preferences, user_id)
    else:  # v3
        recommendations = recommender.get_recommendations_v3(user_preferences, user_id)
    
    # Interakció naplózása
    db.log_interaction(user_id, 'view_recommendations', 
                      data={'version': version, 'recommendation_count': len(recommendations)})
    
    # VERZIÓ INFORMÁCIÓT NEM ADJUK ÁT
    return render_template('user_study/study.html', 
                         recommendations=recommendations)

@user_study_bp.route('/rate_recipe', methods=['POST'])
def rate_recipe():
    """Recept értékelése teljesítmény tracking-gel"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    version = get_user_version()
    recipe_id = int(request.json.get('recipe_id'))
    rating = int(request.json.get('rating'))
    explanation_helpful = request.json.get('explanation_helpful')
    view_time = request.json.get('view_time_seconds', 0)
    interaction_order = request.json.get('interaction_order', 0)
    
    # Értékelés mentése
    db.log_interaction(user_id, 'rate_recipe', 
                      recipe_id=recipe_id, 
                      rating=rating,
                      explanation_helpful=explanation_helpful,
                      view_time=view_time,
                      interaction_order=interaction_order)
    
    # Teljesítmény frissítése
    update_recipe_performance(recipe_id, rating, version)
    
    return jsonify({'status': 'success'})

@user_study_bp.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    """Záró kérdőív"""
    if 'user_id' not in session:
        return redirect(url_for('user_study.register'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        
        # Válaszok mentése
        conn = db.get_connection()
        for key, value in request.form.items():
            if key.startswith('q_'):
                conn.execute('''
                    INSERT INTO questionnaire_responses (user_id, question_key, response)
                    VALUES (?, ?, ?)
                ''', (user_id, key, value))
        
        conn.commit()
        conn.close()
        
        # Befejezés naplózása
        db.log_interaction(user_id, 'complete_study')
        
        return redirect(url_for('user_study.thank_you'))
    
    return render_template('user_study/questionnaire.html')

@user_study_bp.route('/thank_you')
def thank_you():
    """Köszönet oldal"""
    return render_template('user_study/thank_you.html')

@user_study_bp.route('/admin/stats')
def admin_stats():
    """Admin statisztikák - fejlesztéshez"""
    try:
        conn = db.get_connection()
        
        # Alapstatisztikák
        total_users = conn.execute('SELECT COUNT(*) as count FROM users').fetchone()['count']
        total_interactions = conn.execute('SELECT COUNT(*) as count FROM interactions').fetchone()['count']
        
        # Verzió megoszlás
        version_stats = conn.execute('''
            SELECT version, COUNT(*) as count 
            FROM users 
            GROUP BY version
        ''').fetchall()
        
        # Átlagos értékelések verzió szerint
        rating_stats = conn.execute('''
            SELECT version, AVG(rating) as avg_rating, COUNT(*) as count
            FROM interactions 
            WHERE rating IS NOT NULL 
            GROUP BY version
        ''').fetchall()
        
        conn.close()
        
        return render_template('user_study/admin_stats.html',
                             total_users=total_users,
                             total_interactions=total_interactions,
                             version_stats=version_stats,
                             rating_stats=rating_stats)
    except Exception as e:
        return f"Stats error: {e}"

# Blueprint exportálása - KRITIKUS!
__all__ = ['user_study_bp']
