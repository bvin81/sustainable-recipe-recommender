#!/usr/bin/env python3
"""
JAVÍTOTT User Study System - Adatbázis séma és form mezők szinkronizálása
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

# Blueprint létrehozása
user_study_bp = Blueprint('user_study', __name__, 
                         url_prefix='',
                         template_folder='templates')

class DatabaseManager:
    """JAVÍTOTT Adatbázis kezelő osztály"""
    
    def __init__(self, db_path="user_study.db"):
        self.db_path = db_path
        self.init_database()
    
    def get_connection(self):
        """Adatbázis kapcsolat létrehozása"""
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        return conn
    
    def init_database(self):
        """JAVÍTOTT Adatbázis táblák inicializálása - register.html-lel szinkronban"""
        conn = self.get_connection()
        
        # JAVÍTOTT felhasználók tábla - register.html mezőkkel összhangban
        conn.execute('''
            CREATE TABLE IF NOT EXISTS participants (
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
        
        # Interakciók tábla
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
        
        # Kérdőív válaszok tábla
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
        print("✅ Database tables initialized successfully")
    
    def log_interaction(self, user_id, recipe_id, rating=None, 
                       explanation_helpful=None, view_time=None, 
                       interaction_order=None):
        """Felhasználói interakció naplózása"""
        try:
            conn = self.get_connection()
            conn.execute('''
                INSERT INTO interactions 
                (user_id, recipe_id, rating, explanation_helpful, 
                 view_time_seconds, interaction_order)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (user_id, recipe_id, rating, explanation_helpful, 
                  view_time, interaction_order))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Interaction logging error: {e}")

class EnhancedRecipeRecommender:
    """Továbbfejlesztett recept ajánló rendszer"""
    
    def __init__(self):
        self.recipes_df = self.load_hungarian_recipes()
    
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
        
        return pd.DataFrame(hungarian_recipes)
    
    def get_recommendations(self, user_id, version):
        """Ajánlások lekérése verzió alapján"""
        if version == 'v1':
            # V1: Random selection
            sample_size = min(5, len(self.recipes_df))
            recommendations = self.recipes_df.sample(n=sample_size, random_state=42).to_dict('records')
        elif version == 'v2':
            # V2: Composite score alapú
            sorted_recipes = self.recipes_df.sort_values('composite_score', ascending=False)
            recommendations = sorted_recipes.head(5).to_dict('records')
        else:  # v3
            # V3: Composite score + magyarázatok
            sorted_recipes = self.recipes_df.sort_values('composite_score', ascending=False)
            recommendations = sorted_recipes.head(5).to_dict('records')
            # Magyarázatok hozzáadása
            for rec in recommendations:
                rec['explanation'] = self.generate_explanation(rec, version)
        
        return recommendations
    
    def generate_explanation(self, recipe, version):
        """Magyarázat generálása recepthez"""
        if version == 'v2':
            # Rövid magyarázat
            if recipe['composite_score'] > 75:
                return "Ez a recept kiváló összetevőkkel rendelkezik és kiegyensúlyozott."
            elif recipe['composite_score'] > 65:
                return "Jó választás, egészséges és környezetbarát összetevőkkel."
            else:
                return "Hagyományos recept, népszerű és kipróbált."
        
        elif version == 'v3':
            # Részletes magyarázat
            explanations = []
            
            if recipe['HSI'] > 70:
                explanations.append("🍎 <strong>Egészséges:</strong> Magas tápértékű összetevők, kiegyensúlyozott makrotápanyagok")
            
            if recipe['ESI'] > 70:
                explanations.append("🌱 <strong>Környezetbarát:</strong> Alacsony szén-lábnyom, helyi alapanyagok előnyben részesítése")
            
            if recipe['PPI'] > 80:
                explanations.append("⭐ <strong>Népszerű:</strong> Sokan kedvelik és gyakran elkészítik")
            
            if recipe['composite_score'] > 75:
                explanations.append("🎯 <strong>Kiváló választás:</strong> A három szempont alapján optimális recept")
            
            if not explanations:
                explanations.append("📊 Kiegyensúlyozott recept minden szempontból")
            
            return "<br>".join(explanations)
        
        return ""

# Global objektumok inicializálása
db = DatabaseManager()
recommender = EnhancedRecipeRecommender()

def get_user_version():
    """Felhasználó verziójának meghatározása"""
    if 'version' not in session:
        versions = ['v1', 'v2', 'v3']
        session['version'] = random.choice(versions)
    return session['version']

# Blueprint Route-ok

@user_study_bp.route('/')
def welcome():
    """Üdvözlő oldal"""
    return render_template('user_study/welcome.html')

@user_study_bp.route('/register', methods=['GET', 'POST'])
def register():
    """JAVÍTOTT Felhasználó regisztráció"""
    if request.method == 'POST':
        try:
            # JAVÍTOTT mezőnevek a register.html-nek megfelelően
            age_group = request.form.get('age_group')
            education = request.form.get('education')
            cooking_frequency = request.form.get('cooking_frequency')
            sustainability_awareness = int(request.form.get('sustainability_awareness', 3))
            
            # Consent mezők
            consent_participation = bool(request.form.get('consent_participation'))
            consent_data = bool(request.form.get('consent_data'))
            consent_publication = bool(request.form.get('consent_publication'))
            consent_contact = bool(request.form.get('consent_contact'))
            
            # Validáció
            if not all([age_group, education, cooking_frequency]):
                return render_template('user_study/register.html', 
                                     error='Kérjük töltse ki az összes kötelező mezőt.')
            
            if not all([consent_participation, consent_data, consent_publication]):
                return render_template('user_study/register.html', 
                                     error='A kötelező beleegyezések szükségesek a folytatáshoz.')
            
            # Verzió hozzárendelése
            version = get_user_version()
            
            # Felhasználó mentése adatbázisba
            conn = db.get_connection()
            cursor = conn.execute('''
                INSERT INTO participants 
                (age_group, education, cooking_frequency, sustainability_awareness,
                 consent_participation, consent_data, consent_publication, consent_contact, version)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (age_group, education, cooking_frequency, sustainability_awareness,
                  consent_participation, consent_data, consent_publication, consent_contact, version))
            
            user_id = cursor.lastrowid
            conn.commit()
            conn.close()
            
            # Session beállítása
            session['user_id'] = user_id
            session['version'] = version
            session['registration_time'] = datetime.datetime.now().isoformat()
            
            print(f"✅ User registered successfully: ID={user_id}, Version={version}")
            
            return redirect(url_for('user_study.instructions'))
            
        except Exception as e:
            print(f"Registration error: {e}")
            return render_template('user_study/register.html', 
                                 error='Regisztráció sikertelen. Kérjük próbálja újra.')
    
    return render_template('user_study/register.html')

@user_study_bp.route('/instructions')
def instructions():
    """Instrukciók oldal"""
    if 'user_id' not in session:
        return redirect(url_for('user_study.register'))
    
    # VERZIÓ ELREJTÉSE - nem adjuk át a template-nek
    return render_template('user_study/instructions_hidden.html')

@user_study_bp.route('/study')
def study():
    """Fő tanulmány oldal"""
    if 'user_id' not in session:
        return redirect(url_for('user_study.register'))
    
    user_id = session['user_id']
    version = get_user_version()
    
    # Ajánlások lekérése
    recommendations = recommender.get_recommendations(user_id, version)
    
    print(f"✅ Study loaded for user {user_id}, version {version}, {len(recommendations)} recommendations")
    
    # VERZIÓ ELREJTÉSE - study_enhanced.html használata verzió nélkül
    return render_template('user_study/study_enhanced.html', 
                         recommendations=recommendations)

@user_study_bp.route('/rate_recipe', methods=['POST'])
def rate_recipe():
    """Recept értékelése"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        user_id = session['user_id']
        recipe_id = int(request.json.get('recipe_id'))
        rating = int(request.json.get('rating'))
        explanation_helpful = request.json.get('explanation_helpful')
        view_time = request.json.get('view_time_seconds', 0)
        interaction_order = request.json.get('interaction_order', 0)
        
        # Értékelés mentése
        db.log_interaction(user_id, recipe_id, rating=rating,
                          explanation_helpful=explanation_helpful,
                          view_time=view_time,
                          interaction_order=interaction_order)
        
        print(f"✅ Recipe rated: User={user_id}, Recipe={recipe_id}, Rating={rating}")
        
        return jsonify({'status': 'success'})
        
    except Exception as e:
        print(f"Rating error: {e}")
        return jsonify({'error': str(e)}), 500

@user_study_bp.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    """JAVÍTOTT Záró kérdőív"""
    if 'user_id' not in session:
        return redirect(url_for('user_study.register'))
    
    version = get_user_version()
    
    if request.method == 'POST':
        try:
            user_id = session['user_id']
            
            # Válaszok gyűjtése
            system_usability = int(request.form.get('system_usability'))
            recommendation_quality = int(request.form.get('recommendation_quality'))
            trust_level = int(request.form.get('trust_level'))
            explanation_clarity = request.form.get('explanation_clarity')
            sustainability_importance = int(request.form.get('sustainability_importance'))
            overall_satisfaction = int(request.form.get('overall_satisfaction'))
            additional_comments = request.form.get('additional_comments', '')
            
            # explanation_clarity kezelése (v1-nél nincs)
            explanation_clarity_int = int(explanation_clarity) if explanation_clarity else None
            
            # Válaszok mentése
            conn = db.get_connection()
            conn.execute('''
                INSERT INTO questionnaire 
                (user_id, system_usability, recommendation_quality, trust_level, 
                 explanation_clarity, sustainability_importance, overall_satisfaction, additional_comments)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (user_id, system_usability, recommendation_quality, trust_level,
                  explanation_clarity_int, sustainability_importance, overall_satisfaction, additional_comments))
            
            # Befejezés jelölése
            conn.execute('''
                UPDATE participants SET is_completed = 1 WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
            
            print(f"✅ Questionnaire completed for user {user_id}")
            
            return redirect(url_for('user_study.thank_you'))
            
        except Exception as e:
            print(f"Questionnaire error: {e}")
            return render_template('user_study/questionnaire.html', 
                                 version=version,
                                 error='Kérdőív mentése sikertelen. Kérjük próbálja újra.')
    
    return render_template('user_study/questionnaire.html', version=version)

@user_study_bp.route('/thank_you')
def thank_you():
    """Köszönet oldal"""
    version = get_user_version()
    return render_template('user_study/thank_you.html', version=version)

@user_study_bp.route('/admin/stats')
def admin_stats():
    """Valós idejű admin statisztikák"""
    try:
        conn = db.get_connection()
        
        # Alapstatisztikák
        stats = {}
        
        # Összes résztvevő
        total_participants = conn.execute('SELECT COUNT(*) as count FROM participants').fetchone()['count']
        stats['total_participants'] = total_participants
        
        # Befejezett résztvevők
        completed_participants = conn.execute(
            'SELECT COUNT(*) as count FROM participants WHERE is_completed = 1'
        ).fetchone()['count']
        stats['completed_participants'] = completed_participants
        
        # Befejezési arány
        stats['completion_rate'] = completed_participants / total_participants if total_participants > 0 else 0
        
        # Verzió eloszlás
        version_distribution = []
        version_data = conn.execute('''
            SELECT version, 
                   COUNT(*) as count,
                   SUM(CASE WHEN is_completed = 1 THEN 1 ELSE 0 END) as completed
            FROM participants 
            GROUP BY version
        ''').fetchall()
        
        for row in version_data:
            version_distribution.append({
                'version': row['version'],
                'count': row['count'],
                'completed': row['completed']
            })
        
        stats['version_distribution'] = version_distribution
        
        # Átlagos értékelések
        rating_data = conn.execute('''
            SELECT p.version, AVG(i.rating) as avg_rating, COUNT(*) as count
            FROM interactions i
            JOIN participants p ON i.user_id = p.user_id
            WHERE i.rating IS NOT NULL
            GROUP BY p.version
        ''').fetchall()
        
        average_ratings = []
        for row in rating_data:
            average_ratings.append({
                'version': row['version'],
                'avg_rating': row['avg_rating'],
                'count': row['count']
            })
        
        stats['average_ratings'] = average_ratings
        
        # Kérdőív eredmények
        questionnaire_data = conn.execute('''
            SELECT p.version,
                   AVG(q.system_usability) as avg_usability,
                   AVG(q.recommendation_quality) as avg_quality,
                   AVG(q.trust_level) as avg_trust,
                   AVG(q.explanation_clarity) as avg_clarity,
                   AVG(q.overall_satisfaction) as avg_satisfaction
            FROM questionnaire q
            JOIN participants p ON q.user_id = p.user_id
            GROUP BY p.version
        ''').fetchall()
        
        questionnaire_results = []
        for row in questionnaire_data:
            questionnaire_results.append({
                'version': row['version'],
                'avg_usability': row['avg_usability'],
                'avg_quality': row['avg_quality'],
                'avg_trust': row['avg_trust'],
                'avg_clarity': row['avg_clarity'],
                'avg_satisfaction': row['avg_satisfaction']
            })
        
        stats['questionnaire_results'] = questionnaire_results
        
        # Átlagos interakciók/felhasználó
        total_interactions = conn.execute('SELECT COUNT(*) as count FROM interactions').fetchone()['count']
        stats['avg_interactions_per_user'] = total_interactions / total_participants if total_participants > 0 else 0
        
        conn.close()
        
        return render_template('user_study/admin_stats.html', stats=stats)
        
    except Exception as e:
        return f"Stats error: {e}", 500

# Blueprint exportálása
__all__ = ['user_study_bp']
