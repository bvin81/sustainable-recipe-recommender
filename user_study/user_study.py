#!/usr/bin/env python3
"""
Továbbfejlesztett Sustainable Recipe Recommender - User Study System
Valós magyar receptekkel, elrejtett verzió információval és teljesítmény metrikákkal
"""

import os
import sys
import json
import hashlib
import sqlite3
import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import secrets
import random

import pandas as pd
import numpy as np
from flask import Flask, request, render_template, redirect, url_for, session, jsonify, flash
from sklearn.metrics import precision_score, recall_score, f1_score, confusion_matrix

# Project path setup
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', secrets.token_hex(32))

class UserStudyDatabase:
    """SQLite adatbázis kezelő a felhasználói tanulmányhoz"""
    
    def __init__(self, db_path: str = "user_study.db"):
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Adatbázis táblák inicializálása"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        # Participants tábla - VERZIÓ ELREJTÉSE
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS participants (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT UNIQUE NOT NULL,
                version TEXT NOT NULL,
                age_group TEXT,
                education TEXT,
                cooking_frequency TEXT,
                sustainability_awareness INTEGER,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                completed_at TIMESTAMP NULL,
                is_completed BOOLEAN DEFAULT FALSE,
                session_data TEXT  -- JSON a teljes session adatokhoz
            )
        ''')
        
        # Interactions tábla - bővített információkkal
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                recipe_id INTEGER,
                rating INTEGER,
                explanation_helpful INTEGER,
                view_time_seconds REAL,  -- Mennyi ideig nézte
                interaction_order INTEGER,  -- Hanyadik recept
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data TEXT,
                FOREIGN KEY (user_id) REFERENCES participants (user_id)
            )
        ''')
        
        # Recipe performance tracking
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS recipe_performance (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                recipe_id INTEGER NOT NULL,
                version TEXT NOT NULL,
                total_views INTEGER DEFAULT 0,
                total_ratings INTEGER DEFAULT 0,
                avg_rating REAL DEFAULT 0,
                total_positive_ratings INTEGER DEFAULT 0,  -- 4-5 csillag
                precision_score REAL DEFAULT 0,
                recall_score REAL DEFAULT 0,
                f1_score REAL DEFAULT 0,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        
        # Final questionnaire tábla
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS questionnaire (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                system_usability INTEGER,
                recommendation_quality INTEGER,
                trust_level INTEGER,
                explanation_clarity INTEGER,
                sustainability_importance INTEGER,
                overall_satisfaction INTEGER,
                perceived_personalization INTEGER,  -- Mennyire érezte személyre szabottnak
                would_use_again INTEGER,  -- Használná-e újra
                additional_comments TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES participants (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_participant(self, user_id: str, version: str, demographics: Dict) -> bool:
        """Új résztvevő hozzáadása - VERZIÓ ELREJTÉSE"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Session adatok tárolása
            session_data = {
                'demographics': demographics,
                'start_time': datetime.datetime.now().isoformat(),
                'version_hidden': True  # Jelezzük hogy a verzió el van rejtve
            }
            
            cursor.execute('''
                INSERT INTO participants 
                (user_id, version, age_group, education, cooking_frequency, 
                 sustainability_awareness, session_data)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, version,
                demographics.get('age_group'),
                demographics.get('education'),
                demographics.get('cooking_frequency'),
                demographics.get('sustainability_awareness'),
                json.dumps(session_data)
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False
    
    def log_interaction(self, user_id: str, action_type: str, **kwargs):
        """Felhasználói interakció naplózása bővített adatokkal"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO interactions 
                (user_id, action_type, recipe_id, rating, explanation_helpful, 
                 view_time_seconds, interaction_order, data)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                user_id, action_type,
                kwargs.get('recipe_id'),
                kwargs.get('rating'),
                kwargs.get('explanation_helpful'),
                kwargs.get('view_time_seconds'),
                kwargs.get('interaction_order'),
                json.dumps(kwargs.get('data', {}))
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Interaction logging error: {e}")
    
    def update_recipe_performance(self, recipe_id: int, version: str, rating: int):
        """Recept teljesítmény metrikák frissítése"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Létező performance rekord keresése
            cursor.execute('''
                SELECT * FROM recipe_performance 
                WHERE recipe_id = ? AND version = ?
            ''', (recipe_id, version))
            
            existing = cursor.fetchone()
            
            if existing:
                # Frissítés
                new_total_ratings = existing[3] + 1
                new_avg_rating = ((existing[4] * existing[3]) + rating) / new_total_ratings
                new_positive = existing[5] + (1 if rating >= 4 else 0)
                
                cursor.execute('''
                    UPDATE recipe_performance 
                    SET total_ratings = ?, avg_rating = ?, total_positive_ratings = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE recipe_id = ? AND version = ?
                ''', (new_total_ratings, new_avg_rating, new_positive, recipe_id, version))
            else:
                # Új rekord
                cursor.execute('''
                    INSERT INTO recipe_performance 
                    (recipe_id, version, total_views, total_ratings, avg_rating, total_positive_ratings)
                    VALUES (?, ?, 1, 1, ?, ?)
                ''', (recipe_id, version, rating, 1 if rating >= 4 else 0))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Performance update error: {e}")

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
                'HSI': 85.0, 'ESI': 80.0, 'PPI': 70.0, 'composite_score': 79.0
            },
            {
                'recipeid': 4,
                'title': 'Halászlé Szegedi Módra',
                'ingredients': 'ponty, csuka, harcsa, hagyma, paprika, paradicsom, só, borsjuk',
                'instructions': '1. A halakat megtisztítjuk 2. Erős halászlé alapot főzünk 3. Beletesszük a halakat',
                'images': '/static/images/halaszle.jpg',
                'HSI': 80.0, 'ESI': 70.0, 'PPI': 75.0, 'composite_score': 75.0
            },
            {
                'recipeid': 5,
                'title': 'Túrós Csusza',
                'ingredients': 'széles metélt, túró, tejföl, szalonna, hagyma, só, bors',
                'instructions': '1. A tésztát megfőzzük 2. A szalonnát kisütjük 3. Összekeverjük a túróval és tejföllel',
                'images': '/static/images/turos_csusza.jpg',
                'HSI': 65.0, 'ESI': 55.0, 'PPI': 80.0, 'composite_score': 64.0
            }
        ]
        
        return pd.DataFrame(hungarian_recipes)
    
    def get_recommendations_v1(self, user_preferences: Dict, user_id: str) -> List[Dict]:
        """V1: Baseline - népszerűség alapú (PPI score)"""
        # Top receptek PPI szerint
        sample_size = min(5, len(self.recipes_df))
        recommendations = self.recipes_df.nlargest(sample_size, 'PPI').to_dict('records')
        
        for i, rec in enumerate(recommendations):
            rec['explanation'] = f"Népszerű választás ({rec['PPI']:.0f}/100 pont)"
            rec['version'] = 'v1'
            rec['rank'] = i + 1
            
            # Teljesítmény tracking
            self.track_recommendation(user_id, 'v1', rec['recipeid'])
        
        return recommendations
    
    def get_recommendations_v2(self, user_preferences: Dict, user_id: str) -> List[Dict]:
        """V2: Hybrid - kompozit score alapú"""
        # Top receptek kompozit score szerint
        sample_size = min(5, len(self.recipes_df))
        recommendations = self.recipes_df.nlargest(sample_size, 'composite_score').to_dict('records')
        
        for i, rec in enumerate(recommendations):
            rec['explanation'] = f"Kiegyensúlyozott választás (Összpontszám: {rec['composite_score']:.0f}/100)"
            rec['version'] = 'v2'
            rec['rank'] = i + 1
            
            # Teljesítmény tracking
            self.track_recommendation(user_id, 'v2', rec['recipeid'])
        
        return recommendations
    
    def get_recommendations_v3(self, user_preferences: Dict, user_id: str) -> List[Dict]:
        """V3: Hybrid XAI - részletes magyarázatokkal"""
        # Ugyanaz mint V2, de részletes magyarázatokkal
        sample_size = min(5, len(self.recipes_df))
        recommendations = self.recipes_df.nlargest(sample_size, 'composite_score').to_dict('records')
        
        for i, rec in enumerate(recommendations):
            # Részletes magyarázat generálása
            health_desc = self.get_health_description(rec['HSI'])
            env_desc = self.get_environmental_description(rec['ESI'])
            pop_desc = self.get_popularity_description(rec['PPI'])
            
            rec['explanation'] = f"""
            <div class="explanation-detailed">
                <strong>🎯 Miért ajánljuk ezt a receptet:</strong><br><br>
                
                <div class="explanation-item">
                    <span class="explanation-icon">🏥</span>
                    <strong>Egészség ({rec['HSI']:.0f}/100):</strong> {health_desc}
                </div>
                
                <div class="explanation-item">
                    <span class="explanation-icon">🌱</span>
                    <strong>Környezet ({rec['ESI']:.0f}/100):</strong> {env_desc}
                </div>
                
                <div class="explanation-item">
                    <span class="explanation-icon">⭐</span>
                    <strong>Népszerűség ({rec['PPI']:.0f}/100):</strong> {pop_desc}
                </div>
                
                <div class="explanation-summary">
                    <strong>📊 Összesített pontszám:</strong> {rec['composite_score']:.0f}/100
                </div>
            </div>
            """
            rec['version'] = 'v3'
            rec['rank'] = i + 1
            
            # Teljesítmény tracking
            self.track_recommendation(user_id, 'v3', rec['recipeid'])
        
        return recommendations
    
    def get_health_description(self, score: float) -> str:
        """Egészség pontszám leírása"""
        if score >= 80:
            return "Kiváló táplálkozási érték, gazdag vitaminokban és ásványi anyagokban"
        elif score >= 65:
            return "Jó táplálkozási érték, egészséges választás"
        elif score >= 50:
            return "Közepes táplálkozási érték, mérsékelten fogyasztva ajánlott"
        else:
            return "Alacsonyabb táplálkozási érték, alkalmi fogyasztásra"
    
    def get_environmental_description(self, score: float) -> str:
        """Környezeti pontszám leírása"""
        if score >= 75:
            return "Környezetbarát, alacsony ökológiai lábnyom"
        elif score >= 60:
            return "Mérsékelten környezetbarát, fenntartható választás"
        elif score >= 45:
            return "Közepes környezeti hatás"
        else:
            return "Magasabb környezeti terhelés"
    
    def get_popularity_description(self, score: float) -> str:
        """Népszerűség pontszám leírása"""
        if score >= 85:
            return "Rendkívül népszerű, sokan kedvelik"
        elif score >= 70:
            return "Népszerű választás"
        elif score >= 55:
            return "Közepesen kedvelt"
        else:
            return "Specifikus ízlésvilágnak szól"
    
    def track_recommendation(self, user_id: str, version: str, recipe_id: int):
        """Ajánlás tracking teljesítmény méréshez"""
        if user_id not in self.performance_tracker:
            self.performance_tracker[user_id] = {
                'version': version,
                'recommended_recipes': [],
                'start_time': datetime.datetime.now()
            }
        
        self.performance_tracker[user_id]['recommended_recipes'].append({
            'recipe_id': recipe_id,
            'recommended_at': datetime.datetime.now()
        })
    
    def calculate_precision_recall(self, user_id: str, positive_ratings: List[int]) -> Dict:
        """Precision, Recall, F1 score számítása"""
        if user_id not in self.performance_tracker:
            return {'precision': 0, 'recall': 0, 'f1': 0}
        
        # Ajánlott receptek
        recommended_recipes = [r['recipe_id'] for r in self.performance_tracker[user_id]['recommended_recipes']]
        
        # Pozitív értékelések (4-5 csillag)
        positive_recipe_ids = [recommended_recipes[i] for i, rating in enumerate(positive_ratings) if rating >= 4]
        
        if len(recommended_recipes) == 0:
            return {'precision': 0, 'recall': 0, 'f1': 0}
        
        # True Positives: ajánlott ÉS pozitívan értékelt
        tp = len(positive_recipe_ids)
        
        # False Positives: ajánlott DE negatívan értékelt
        fp = len(recommended_recipes) - tp
        
        # Precision: TP / (TP + FP)
        precision = tp / len(recommended_recipes) if len(recommended_recipes) > 0 else 0
        
        # Recall: nehezebb meghatározni, mert nem tudjuk az összes "releváns" receptet
        # Közelítjük: TP / (TP + véletlenszerű minta a nem ajánlott receptekből)
        total_available_recipes = len(self.recipes_df)
        estimated_relevant_recipes = total_available_recipes * 0.2  # Becsüljük hogy 20% releváns
        
        recall = tp / estimated_relevant_recipes if estimated_relevant_recipes > 0 else 0
        
        # F1 Score
        f1 = 2 * (precision * recall) / (precision + recall) if (precision + recall) > 0 else 0
        
        return {
            'precision': round(precision, 3),
            'recall': round(recall, 3),
            'f1': round(f1, 3),
            'true_positives': tp,
            'false_positives': fp,
            'recommended_count': len(recommended_recipes)
        }

# Global objektumok
db = UserStudyDatabase()
recommender = EnhancedRecipeRecommender()

def get_user_version() -> str:
    """Véletlenszerű verzió kiosztás A/B/C teszthez - ELREJTVE"""
    if 'version' not in session:
        session['version'] = random.choice(['v1', 'v2', 'v3'])
        # FONTOS: A verzió információt SOHA nem mutatjuk a felhasználónak
    return session['version']

def generate_user_id() -> str:
    """Egyedi, névtelen felhasználó ID generálása"""
    if 'user_id' not in session:
        timestamp = str(datetime.datetime.now().timestamp())
        random_str = secrets.token_hex(8)
        session['user_id'] = hashlib.md5(f"{timestamp}_{random_str}".encode()).hexdigest()[:12]
    return session['user_id']

# ROUTES
@app.route('/')
def welcome():
    """Üdvöző oldal - VERZIÓ INFORMÁCIÓ ELREJTVE"""
    return render_template('user_study/welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Demográfiai adatok és beleegyezés"""
    if request.method == 'POST':
        user_id = generate_user_id()
        version = get_user_version()  # Verzió hozzárendelés, de elrejtve
        
        demographics = {
            'age_group': request.form.get('age_group'),
            'education': request.form.get('education'),
            'cooking_frequency': request.form.get('cooking_frequency'),
            'sustainability_awareness': int(request.form.get('sustainability_awareness', 3))
        }
        
        if db.add_participant(user_id, version, demographics):
            db.log_interaction(user_id, 'registration', data=demographics)
            return redirect(url_for('instructions'))
        else:
            flash('Hiba történt a regisztráció során. Kérjük próbálja újra.')
    
    return render_template('user_study/register.html')

@app.route('/instructions')
def instructions():
    """Instrukciók oldal - VERZIÓ ELREJTÉSE"""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    # Verzió információt NEM adjuk át a template-nek
    return render_template('user_study/instructions_hidden.html')

@app.route('/study')
def study():
    """Fő tanulmány oldal - valós magyar receptekkel"""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
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
    return render_template('user_study/study_enhanced.html', 
                         recommendations=recommendations)

@app.route('/rate_recipe', methods=['POST'])
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
                      view_time_seconds=view_time,
                      interaction_order=interaction_order)
    
    # Teljesítmény metrikák frissítése
    db.update_recipe_performance(recipe_id, version, rating)
    
    return jsonify({'success': True})

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    """Záró kérdőív - bővített kérdésekkel"""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        
        # Teljesítmény metrikák számítása
        ratings = session.get('recipe_ratings', [])
        metrics = recommender.calculate_precision_recall(user_id, ratings)
        
        # Kérdőív válaszok mentése
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO questionnaire 
            (user_id, system_usability, recommendation_quality, trust_level, 
             explanation_clarity, sustainability_importance, overall_satisfaction,
             perceived_personalization, would_use_again, additional_comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            int(request.form.get('system_usability')),
            int(request.form.get('recommendation_quality')),
            int(request.form.get('trust_level')),
            int(request.form.get('explanation_clarity', 3)),
            int(request.form.get('sustainability_importance')),
            int(request.form.get('overall_satisfaction')),
            int(request.form.get('perceived_personalization', 3)),
            int(request.form.get('would_use_again', 3)),
            request.form.get('additional_comments', '')
        ))
        
        conn.commit()
        conn.close()
        
        # Résztvevő befejezettként jelölése
        db.complete_participant(user_id)
        
        # Metrikák session-be mentése
        session['performance_metrics'] = metrics
        
        return redirect(url_for('thank_you'))
    
    return render_template('user_study/questionnaire_enhanced.html')

@app.route('/thank_you')
def thank_you():
    """Köszönjük oldal - teljesítmény metrikákkal"""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    metrics = session.get('performance_metrics', {})
    return render_template('user_study/thank_you_enhanced.html', metrics=metrics)

@app.route('/admin/stats')
def admin_stats():
    """Adminisztrátori statisztikák - teljesítmény metrikákkal"""
    try:
        conn = sqlite3.connect(db.db_path)
        
        # Alapstatisztikák
        stats = {}
        
        # Résztvevők száma verzió szerint
        version_counts = pd.read_sql_query('''
            SELECT version, COUNT(*) as count, 
                   SUM(CASE WHEN is_completed THEN 1 ELSE 0 END) as completed
            FROM participants 
            GROUP BY version
        ''', conn)
        
        stats['version_distribution'] = version_counts.to_dict('records')
        
        # Teljesítmény metrikák verzió szerint
        performance_data = pd.read_sql_query('''
            SELECT version, 
                   AVG(precision_score) as avg_precision,
                   AVG(recall_score) as avg_recall,
                   AVG(f1_score) as avg_f1,
                   COUNT(*) as recipe_count
            FROM recipe_performance 
            GROUP BY version
        ''', conn)
        
        stats['performance_metrics'] = performance_data.to_dict('records')
        
        # További statisztikák...
        conn.close()
        
        return render_template('user_study/admin_stats_enhanced.html', stats=stats)
        
    except Exception as e:
        return f"Statistics error: {e}", 500

@app.route('/admin/metrics')
def admin_metrics():
    """Részletes teljesítmény metrikák"""
    try:
        conn = sqlite3.connect(db.db_path)
        
        # Precision/Recall/F1 adatok
        metrics_data = pd.read_sql_query('''
            SELECT r.version, r.recipe_id, r.precision_score, r.recall_score, r.f1_score,
                   r.total_ratings, r.avg_rating, rec.title
            FROM recipe_performance r
            LEFT JOIN (SELECT recipeid, title FROM processed_recipes LIMIT 100) rec 
                ON r.recipe_id = rec.recipeid
            ORDER BY r.f1_score DESC
        ''', conn)
        
        conn.close()
        
        return jsonify(metrics_data.to_dict('records'))
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    # Development szerver
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
