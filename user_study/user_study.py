#!/usr/bin/env python3
"""
Enhanced User Study System - Működő verzió képekkel
Template path fix + CSV képek megjelenítése
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
from flask import Flask, Blueprint, render_template, request, session, redirect, url_for, jsonify, g

# Project path setup
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# Blueprint létrehozása - TEMPLATE PATH JAVÍTÁS!
user_study_bp = Blueprint('user_study', __name__, 
                         url_prefix='',
                         template_folder='templates/user_study')  # KULCS!

class UserStudyDatabase:
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
        
        # Participants tábla
        conn.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                user_id INTEGER PRIMARY KEY AUTOINCREMENT,
                age_group TEXT NOT NULL,
                education TEXT NOT NULL,
                cooking_frequency TEXT NOT NULL,
                sustainability_awareness INTEGER NOT NULL,
                version TEXT NOT NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Interactions tábla
        conn.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
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
            CREATE TABLE IF NOT EXISTS questionnaire (
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
    
    def create_user(self, age_group, education, cooking_frequency, sustainability_awareness, version):
        """Új felhasználó létrehozása"""
        conn = self.get_connection()
        cursor = conn.execute('''
            INSERT INTO participants (age_group, education, cooking_frequency, sustainability_awareness, version)
            VALUES (?, ?, ?, ?, ?)
        ''', (age_group, education, cooking_frequency, sustainability_awareness, version))
        
        user_id = cursor.lastrowid
        conn.commit()
        conn.close()
        return user_id
    
    def log_interaction(self, user_id, recipe_id, rating, explanation_helpful=None, view_time=None, interaction_order=None):
        """Interakció naplózása"""
        conn = self.get_connection()
        conn.execute('''
            INSERT INTO interactions (user_id, recipe_id, rating, explanation_helpful, view_time_seconds, interaction_order)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', (user_id, recipe_id, rating, explanation_helpful, view_time, interaction_order))
        
        conn.commit()
        conn.close()
    
    def save_questionnaire(self, user_id, responses):
        """Kérdőív válaszok mentése"""
        conn = self.get_connection()
        conn.execute('''
            INSERT INTO questionnaire 
            (user_id, system_usability, recommendation_quality, trust_level, 
             explanation_clarity, sustainability_importance, overall_satisfaction, additional_comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            responses.get('system_usability'),
            responses.get('recommendation_quality'),
            responses.get('trust_level'),
            responses.get('explanation_clarity'),
            responses.get('sustainability_importance'),
            responses.get('overall_satisfaction'),
            responses.get('additional_comments', '')
        ))
        
        # Mark user as completed
        conn.execute('''
            UPDATE participants SET is_completed = TRUE WHERE user_id = ?
        ''', (user_id,))
        
        conn.commit()
        conn.close()

class EnhancedRecipeRecommender:
    """Továbbfejlesztett recept ajánló rendszer - KÉPEKKEL"""
    
    def __init__(self):
        self.recipes_df = self.load_hungarian_recipes()
        print(f"✅ Receptek betöltve: {len(self.recipes_df) if self.recipes_df is not None else 0}")
    
    def load_hungarian_recipes(self) -> pd.DataFrame:
        """Magyar receptek betöltése - KÉPEKKEL"""
        try:
            csv_path = project_root / "data" / "processed_recipes.csv"
            if csv_path.exists():
                df = pd.read_csv(csv_path)
                print(f"✅ CSV betöltve: {len(df)} recept")
                
                # Képek ellenőrzése
                if 'images' in df.columns:
                    print(f"🖼️ Képek oszlop megtalálva")
                    # Debug: első kép URL
                    if len(df) > 0:
                        first_image = df['images'].iloc[0]
                        print(f"🔍 Első kép URL: {first_image}")
                else:
                    print("⚠️ Nincs 'images' oszlop")
                
                return df
            else:
                print("⚠️ processed_recipes.csv nem található, sample adatok")
                return self.create_sample_data()
        except Exception as e:
            print(f"❌ CSV betöltési hiba: {e}")
            return self.create_sample_data()
    
    def create_sample_data(self) -> pd.DataFrame:
        """Sample adatok KÜLSŐ KÉPEKKEL"""
        sample_recipes = [
            {
                'recipeid': 1,
                'title': 'Hagyományos Gulyásleves',
                'ingredients': 'marhahús, hagyma, paprika, paradicsom, burgonya, fokhagyma, kömény, majoranna',
                'instructions': '1. A húst kockákra vágjuk és enyhén megsózzuk. 2. Megdinszteljük a hagymát, hozzáadjuk a paprikát. 3. Felöntjük vízzel és főzzük 1.5 órát.',
                'images': 'https://images.unsplash.com/photo-1547592180-85f173990554?w=400',
                'HSI': 75.0, 'ESI': 60.0, 'PPI': 90.0, 'composite_score': 71.0
            },
            {
                'recipeid': 2,
                'title': 'Rántott Schnitzel Burgonyával', 
                'ingredients': 'sertéshús, liszt, tojás, zsemlemorzsa, burgonya, olaj, só, bors',
                'instructions': '1. A húst kikalapáljuk és megsózzuk. 2. Lisztbe, majd tojásba, végül morzsába forgatjuk. 3. Forró olajban kisütjük.',
                'images': 'https://images.unsplash.com/photo-1558030006-450675393462?w=400',
                'HSI': 55.0, 'ESI': 45.0, 'PPI': 85.0, 'composite_score': 57.0
            },
            {
                'recipeid': 3,
                'title': 'Vegetáriánus Lecsó',
                'ingredients': 'paprika, paradicsom, hagyma, tojás, tofu, olívaolaj, só, bors, fokhagyma',
                'instructions': '1. A hagymát megdinszteljük. 2. Hozzáadjuk a paprikát és paradicsomot. 3. Tofuval és tojással dúsítjuk.',
                'images': 'https://images.unsplash.com/photo-1565299624946-b28f40a0ca4b?w=400',
                'HSI': 85.0, 'ESI': 80.0, 'PPI': 70.0, 'composite_score': 78.0
            },
            {
                'recipeid': 4,
                'title': 'Halászlé Szegedi Módra',
                'ingredients': 'ponty, csuka, harcsa, hagyma, paradicsom, paprika, só, babérlevél',
                'instructions': '1. A halakat megtisztítjuk. 2. Erős alapot főzünk a fejekből. 3. A haldarabokat beletesszük és fűszerezzük.',
                'images': 'https://images.unsplash.com/photo-1544943910-4c1dc44aab44?w=400',
                'HSI': 80.0, 'ESI': 70.0, 'PPI': 75.0, 'composite_score': 74.0
            },
            {
                'recipeid': 5,
                'title': 'Túrós Csusza',
                'ingredients': 'széles metélt, túró, tejföl, szalonna, hagyma, só, bors',
                'instructions': '1. A tésztát megfőzzük. 2. A szalonnát kisütjük. 3. Összekeverjük a túróval és tejföllel.',
                'images': 'https://images.unsplash.com/photo-1551698618-1dfe5d97d256?w=400',
                'HSI': 65.0, 'ESI': 55.0, 'PPI': 80.0, 'composite_score': 65.0
            }
        ]
        
        df = pd.DataFrame(sample_recipes)
        print(f"✅ Sample adatok létrehozva: {len(df)} recept")
        return df
    
    def get_recommendations(self, version='v1', n_recommendations=5):
        """Ajánlások lekérése verzió szerint"""
        if self.recipes_df is None or len(self.recipes_df) == 0:
            print("❌ Nincs elérhető recept adat")
            return []
        
        # Véletlenszerű kiválasztás (egyszerű implementáció)
        sample_size = min(n_recommendations, len(self.recipes_df))
        recommendations = self.recipes_df.sample(n=sample_size, random_state=42).to_dict('records')
        
        # Magyarázatok hozzáadása verzió szerint
        for rec in recommendations:
            if version == 'v2' or version == 'v3':
                rec['explanation'] = self.generate_explanation(rec, version)
        
        print(f"✅ {len(recommendations)} ajánlás generálva verzióhoz: {version}")
        return recommendations
    
    def generate_explanation(self, recipe, version):
        """Magyarázat generálása"""
        explanations = []
        
        if recipe['HSI'] > 70:
            explanations.append("🏥 Magas tápérték és egészséges összetevők")
        if recipe['ESI'] > 70:
            explanations.append("🌱 Környezetbarát ingrediensek")
        if recipe['PPI'] > 80:
            explanations.append("⭐ Népszerű és kipróbált recept")
        
        if not explanations:
            explanations.append("🍽️ Kiegyensúlyozott összetétel")
        
        if version == 'v3':
            # Részletesebb magyarázat v3-hoz
            detailed = f"Ez a recept {recipe['composite_score']:.0f}/100 pontot ért el összesített értékelésünkben. "
            detailed += " ".join(explanations)
            return detailed
        else:
            # Rövid magyarázat v2-höz
            return " • ".join(explanations)

# Global objektumok
db = UserStudyDatabase()
recommender = EnhancedRecipeRecommender()

def get_user_version():
    """Verzió kiosztása"""
    if 'version' not in session:
        versions = ['v1', 'v2', 'v3']
        session['version'] = random.choice(versions)
    return session['version']

# ROUTES - Template path javítva!

@user_study_bp.route('/')
def welcome():
    """Üdvözlő oldal"""
    return render_template('welcome.html')

@user_study_bp.route('/register', methods=['GET', 'POST'])
def register():
    """Regisztráció"""
    if request.method == 'POST':
        try:
            age_group = request.form.get('age_group')
            education = request.form.get('education')
            cooking_frequency = request.form.get('cooking_frequency')
            sustainability_awareness = int(request.form.get('sustainability_awareness', 3))
            
            version = get_user_version()
            
            user_id = db.create_user(age_group, education, cooking_frequency, 
                                   sustainability_awareness, version)
            
            session['user_id'] = user_id
            session['version'] = version
            
            return redirect(url_for('user_study.instructions'))
            
        except Exception as e:
            print(f"Registration error: {e}")
            return render_template('register.html', error='Regisztráció sikertelen')
    
    return render_template('register.html')

@user_study_bp.route('/instructions')
def instructions():
    """Instrukciók"""
    if 'user_id' not in session:
        return redirect(url_for('user_study.register'))
    
    version = session.get('version', 'v1')
    return render_template('instructions.html', version=version)

@user_study_bp.route('/study')
def study():
    """Fő tanulmány oldal - KÉPEKKEL"""
    if 'user_id' not in session:
        return redirect(url_for('user_study.register'))
    
    version = session.get('version', 'v1')
    
    # Ajánlások lekérése
    recommendations = recommender.get_recommendations(version=version, n_recommendations=5)
    
    if not recommendations:
        return "Hiba: Nem sikerült betölteni a recepteket", 500
    
    # Debug: képek ellenőrzése
    print(f"🔍 Template-nek átadott ajánlások:")
    for i, rec in enumerate(recommendations):
        print(f"   {i+1}. {rec['title']} - Kép: {rec.get('images', 'NINCS')}")
    
    return render_template('study.html', 
                         recommendations=recommendations, 
                         version=version)

@user_study_bp.route('/rate_recipe', methods=['POST'])
def rate_recipe():
    """Recept értékelése"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    data = request.get_json()
    
    recipe_id = int(data.get('recipe_id'))
    rating = int(data.get('rating'))
    explanation_helpful = data.get('explanation_helpful')
    view_time = data.get('view_time_seconds', 0)
    interaction_order = data.get('interaction_order', 0)
    
    db.log_interaction(user_id, recipe_id, rating, explanation_helpful, view_time, interaction_order)
    
    return jsonify({'status': 'success'})

@user_study_bp.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    """Záró kérdőív"""
    if 'user_id' not in session:
        return redirect(url_for('user_study.register'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        
        responses = {
            'system_usability': request.form.get('system_usability'),
            'recommendation_quality': request.form.get('recommendation_quality'),
            'trust_level': request.form.get('trust_level'),
            'explanation_clarity': request.form.get('explanation_clarity'),
            'sustainability_importance': request.form.get('sustainability_importance'),
            'overall_satisfaction': request.form.get('overall_satisfaction'),
            'additional_comments': request.form.get('additional_comments', '')
        }
        
        db.save_questionnaire(user_id, responses)
        
        return redirect(url_for('user_study.thank_you'))
    
    version = session.get('version', 'v1')
    return render_template('questionnaire.html', version=version)

@user_study_bp.route('/thank_you')
def thank_you():
    """Köszönet oldal"""
    version = session.get('version', 'v1')
    return render_template('thank_you.html', version=version)

@user_study_bp.route('/admin/stats')
def admin_stats():
    """Admin statisztikák"""
    try:
        conn = db.get_connection()
        
        # Alapstatisztikák
        stats = {}
        
        # Résztvevők száma
        result = conn.execute('SELECT COUNT(*) as count FROM participants').fetchone()
        stats['total_participants'] = result['count'] if result else 0
        
        # Befejezett tanulmányok
        result = conn.execute('SELECT COUNT(*) as count FROM participants WHERE is_completed = 1').fetchone()
        stats['completed_participants'] = result['count'] if result else 0
        
        # Befejezési arány
        if stats['total_participants'] > 0:
            stats['completion_rate'] = stats['completed_participants'] / stats['total_participants']
        else:
            stats['completion_rate'] = 0
        
        # Verzió eloszlás
        version_results = conn.execute('''
            SELECT version, 
                   COUNT(*) as count,
                   SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed
            FROM participants 
            GROUP BY version
        ''').fetchall()
        
        stats['version_distribution'] = [dict(row) for row in version_results]
        
        # Átlagos értékelések
        rating_results = conn.execute('''
            SELECT p.version, AVG(i.rating) as avg_rating, COUNT(i.rating) as count
            FROM participants p
            JOIN interactions i ON p.user_id = i.user_id
            WHERE i.rating IS NOT NULL
            GROUP BY p.version
        ''').fetchall()
        
        stats['average_ratings'] = [dict(row) for row in rating_results]
        
        # Kérdőív eredmények
        questionnaire_results = conn.execute('''
            SELECT p.version,
                   AVG(q.system_usability) as avg_usability,
                   AVG(q.recommendation_quality) as avg_quality,
                   AVG(q.trust_level) as avg_trust,
                   AVG(q.explanation_clarity) as avg_clarity,
                   AVG(q.overall_satisfaction) as avg_satisfaction
            FROM participants p
            JOIN questionnaire q ON p.user_id = q.user_id
            GROUP BY p.version
        ''').fetchall()
        
        stats['questionnaire_results'] = [dict(row) for row in questionnaire_results]
        
        # Átlagos interakciók
        interactions_count = conn.execute('SELECT COUNT(*) as count FROM interactions').fetchone()
        if stats['total_participants'] > 0:
            stats['avg_interactions_per_user'] = interactions_count['count'] / stats['total_participants']
        else:
            stats['avg_interactions_per_user'] = 0
        
        conn.close()
        
        return render_template('admin_stats.html', stats=stats)
        
    except Exception as e:
        return f"Stats error: {e}", 500

# Blueprint exportálása
__all__ = ['user_study_bp']
