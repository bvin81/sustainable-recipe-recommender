#!/usr/bin/env python3
"""
Sustainable Recipe Recommender - User Study System
Felhasználói tanulmány három különböző ajánló rendszer verzióval
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
        
        # Participants tábla
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
                is_completed BOOLEAN DEFAULT FALSE
            )
        ''')
        
        # Interactions tábla
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS interactions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                recipe_id INTEGER,
                rating INTEGER,
                explanation_helpful INTEGER,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                data TEXT,
                FOREIGN KEY (user_id) REFERENCES participants (user_id)
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
                additional_comments TEXT,
                timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY (user_id) REFERENCES participants (user_id)
            )
        ''')
        
        conn.commit()
        conn.close()
    
    def add_participant(self, user_id: str, version: str, demographics: Dict) -> bool:
        """Új résztvevő hozzáadása"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO participants 
                (user_id, version, age_group, education, cooking_frequency, sustainability_awareness)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id, version,
                demographics.get('age_group'),
                demographics.get('education'),
                demographics.get('cooking_frequency'),
                demographics.get('sustainability_awareness')
            ))
            
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"Database error: {e}")
            return False
    
    def log_interaction(self, user_id: str, action_type: str, **kwargs):
        """Felhasználói interakció naplózása"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                INSERT INTO interactions 
                (user_id, action_type, recipe_id, rating, explanation_helpful, data)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', (
                user_id, action_type,
                kwargs.get('recipe_id'),
                kwargs.get('rating'),
                kwargs.get('explanation_helpful'),
                json.dumps(kwargs.get('data', {}))
            ))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Interaction logging error: {e}")
    
    def complete_participant(self, user_id: str):
        """Résztvevő befejezettként jelölése"""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute('''
                UPDATE participants 
                SET completed_at = CURRENT_TIMESTAMP, is_completed = TRUE
                WHERE user_id = ?
            ''', (user_id,))
            
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Completion error: {e}")

class RecipeRecommender:
    """Recept ajánló rendszer három verzióval"""
    
    def __init__(self):
        self.recipes_df = self.load_recipes()
    
    def load_recipes(self) -> pd.DataFrame:
        """Recept adatok betöltése"""
        try:
            csv_path = project_root / "data" / "processed_recipes.csv"
            if csv_path.exists():
                return pd.read_csv(csv_path)
            else:
                # Fallback sample data
                return self.create_sample_recipes()
        except Exception as e:
            print(f"Recipe loading error: {e}")
            return self.create_sample_recipes()
    
    def create_sample_recipes(self) -> pd.DataFrame:
        """Sample recept adatok létrehozása"""
        recipes = []
        
        sample_recipes = [
            ("Mediterranean Quinoa Bowl", "quinoa, tomatoes, olives, feta, olive oil", 0.85, 0.70, 0.75),
            ("Grilled Salmon with Vegetables", "salmon, broccoli, carrots, lemon, herbs", 0.90, 0.60, 0.80),
            ("Vegetarian Lentil Curry", "lentils, coconut milk, spices, vegetables", 0.80, 0.85, 0.70),
            ("Chicken Avocado Salad", "chicken breast, avocado, mixed greens, nuts", 0.75, 0.65, 0.85),
            ("Roasted Vegetable Pasta", "whole grain pasta, seasonal vegetables, herbs", 0.70, 0.80, 0.75),
            ("Black Bean Tacos", "black beans, corn tortillas, salsa, avocado", 0.80, 0.75, 0.80),
            ("Asian Tofu Stir-fry", "tofu, mixed vegetables, soy sauce, ginger", 0.85, 0.80, 0.70),
            ("Greek Yogurt Parfait", "greek yogurt, berries, granola, honey", 0.75, 0.70, 0.85),
            ("Stuffed Bell Peppers", "bell peppers, quinoa, vegetables, cheese", 0.80, 0.75, 0.75),
            ("Sweet Potato Buddha Bowl", "sweet potato, chickpeas, greens, tahini", 0.85, 0.80, 0.70)
        ]
        
        for i, (title, ingredients, hsi, esi, ppi) in enumerate(sample_recipes):
            recipes.append({
                'recipeid': i + 1,
                'title': title,
                'ingredients': ingredients,
                'HSI': hsi,
                'ESI': esi, 
                'PPI': ppi
            })
        
        return pd.DataFrame(recipes)
    
    def get_recommendations_v1(self, user_preferences: Dict) -> List[Dict]:
        """V1: Baseline - egyszerű hasonlóság alapú"""
        # Véletlenszerű + népszerűség alapú válogatás
        sample_size = min(5, len(self.recipes_df))
        recommendations = self.recipes_df.nlargest(sample_size, 'PPI').to_dict('records')
        
        for rec in recommendations:
            rec['explanation'] = f"Népszerű recept ({rec['PPI']:.1f}/1.0 pontszám)"
            rec['version'] = 'v1'
        
        return recommendations
    
    def get_recommendations_v2(self, user_preferences: Dict) -> List[Dict]:
        """V2: Hybrid - egészség és környezeti tényezőkkel"""
        # Normalizált composite score
        health_weight = 0.4
        env_weight = 0.4
        pop_weight = 0.2
        
        self.recipes_df['composite_score'] = (
            health_weight * self.recipes_df['HSI'] +
            env_weight * self.recipes_df['ESI'] + 
            pop_weight * self.recipes_df['PPI']
        )
        
        sample_size = min(5, len(self.recipes_df))
        recommendations = self.recipes_df.nlargest(sample_size, 'composite_score').to_dict('records')
        
        for rec in recommendations:
            rec['explanation'] = f"Kiegyensúlyozott választás (Egészség: {rec['HSI']:.1f}, Környezet: {rec['ESI']:.1f})"
            rec['version'] = 'v2'
        
        return recommendations
    
    def get_recommendations_v3(self, user_preferences: Dict) -> List[Dict]:
        """V3: Hybrid XAI - részletes magyarázatokkal"""
        # Ugyanaz mint V2, de gazdagabb magyarázatokkal
        health_weight = 0.4
        env_weight = 0.4
        pop_weight = 0.2
        
        self.recipes_df['composite_score'] = (
            health_weight * self.recipes_df['HSI'] +
            env_weight * self.recipes_df['ESI'] + 
            pop_weight * self.recipes_df['PPI']
        )
        
        sample_size = min(5, len(self.recipes_df))
        recommendations = self.recipes_df.nlargest(sample_size, 'composite_score').to_dict('records')
        
        for rec in recommendations:
            # Részletes magyarázat generálása
            health_desc = "kiváló" if rec['HSI'] > 0.8 else "jó" if rec['HSI'] > 0.6 else "megfelelő"
            env_desc = "környezetbarát" if rec['ESI'] > 0.7 else "mérsékelt hatású" if rec['ESI'] > 0.5 else "átlagos"
            
            rec['explanation'] = f"""
            <strong>Miért ajánljuk:</strong><br>
            🏥 <strong>Egészség:</strong> {health_desc} táplálkozási érték ({rec['HSI']:.1f}/1.0)<br>
            🌱 <strong>Környezet:</strong> {env_desc} környezeti hatás ({rec['ESI']:.1f}/1.0)<br>
            ⭐ <strong>Népszerűség:</strong> {rec['PPI']:.1f}/1.0 értékelés<br>
            <em>Összpontszám: {rec['composite_score']:.2f}/1.0</em>
            """
            rec['version'] = 'v3'
        
        return recommendations

# Global objektumok
db = UserStudyDatabase()
recommender = RecipeRecommender()

def get_user_version() -> str:
    """Véletlenszerű verzió kiosztás A/B/C teszthez"""
    if 'version' not in session:
        session['version'] = random.choice(['v1', 'v2', 'v3'])
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
    """Üdvöző oldal"""
    return render_template('user_study/welcome.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Demográfiai adatok és beleegyezés"""
    if request.method == 'POST':
        # Adatok mentése
        user_id = generate_user_id()
        version = get_user_version()
        
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
    """Instrukciók oldal"""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    version = get_user_version()
    return render_template('user_study/instructions.html', version=version)

@app.route('/study')
def study():
    """Fő tanulmány oldal - ajánlások megjelenítése"""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    user_id = session['user_id']
    version = get_user_version()
    
    # Felhasználói preferenciák (mostanra egyszerű)
    user_preferences = {}
    
    # Ajánlások lekérése verzió alapján
    if version == 'v1':
        recommendations = recommender.get_recommendations_v1(user_preferences)
    elif version == 'v2':
        recommendations = recommender.get_recommendations_v2(user_preferences)
    else:  # v3
        recommendations = recommender.get_recommendations_v3(user_preferences)
    
    # Interakció naplózása
    db.log_interaction(user_id, 'view_recommendations', 
                      data={'version': version, 'recommendation_count': len(recommendations)})
    
    return render_template('user_study/study.html', 
                         recommendations=recommendations, 
                         version=version)

@app.route('/rate_recipe', methods=['POST'])
def rate_recipe():
    """Recept értékelése"""
    if 'user_id' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user_id = session['user_id']
    recipe_id = int(request.json.get('recipe_id'))
    rating = int(request.json.get('rating'))
    explanation_helpful = request.json.get('explanation_helpful')
    
    # Értékelés mentése
    db.log_interaction(user_id, 'rate_recipe', 
                      recipe_id=recipe_id, 
                      rating=rating,
                      explanation_helpful=explanation_helpful)
    
    return jsonify({'success': True})

@app.route('/questionnaire', methods=['GET', 'POST'])
def questionnaire():
    """Záró kérdőív"""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    if request.method == 'POST':
        user_id = session['user_id']
        
        # Kérdőív válaszok mentése
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT INTO questionnaire 
            (user_id, system_usability, recommendation_quality, trust_level, 
             explanation_clarity, sustainability_importance, overall_satisfaction, additional_comments)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            user_id,
            int(request.form.get('system_usability')),
            int(request.form.get('recommendation_quality')),
            int(request.form.get('trust_level')),
            int(request.form.get('explanation_clarity', 3)),
            int(request.form.get('sustainability_importance')),
            int(request.form.get('overall_satisfaction')),
            request.form.get('additional_comments', '')
        ))
        
        conn.commit()
        conn.close()
        
        # Résztvevő befejezettként jelölése
        db.complete_participant(user_id)
        
        return redirect(url_for('thank_you'))
    
    version = get_user_version()
    return render_template('user_study/questionnaire.html', version=version)

@app.route('/thank_you')
def thank_you():
    """Köszönjük oldal"""
    if 'user_id' not in session:
        return redirect(url_for('register'))
    
    version = get_user_version()
    return render_template('user_study/thank_you.html', version=version)

@app.route('/admin/stats')
def admin_stats():
    """Adminisztrátori statisztikák"""
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
        
        # Átlagos értékelések
        ratings = pd.read_sql_query('''
            SELECT p.version, AVG(i.rating) as avg_rating
            FROM participants p
            JOIN interactions i ON p.user_id = i.user_id
            WHERE i.rating IS NOT NULL
            GROUP BY p.version
        ''', conn)
        
        stats['average_ratings'] = ratings.to_dict('records')
        
        # Kérdőív eredmények
        questionnaire_results = pd.read_sql_query('''
            SELECT p.version, 
                   AVG(q.system_usability) as avg_usability,
                   AVG(q.recommendation_quality) as avg_quality,
                   AVG(q.trust_level) as avg_trust,
                   AVG(q.explanation_clarity) as avg_clarity,
                   AVG(q.overall_satisfaction) as avg_satisfaction
            FROM participants p
            JOIN questionnaire q ON p.user_id = q.user_id
            GROUP BY p.version
        ''', conn)
        
        stats['questionnaire_results'] = questionnaire_results.to_dict('records')
        
        conn.close()
        
        return render_template('user_study/admin_stats.html', stats=stats)
        
    except Exception as e:
        return f"Statistics error: {e}", 500

@app.route('/admin/export/<format>')
def export_data(format):
    """Adatok exportálása"""
    if format not in ['csv', 'json']:
        return "Invalid format", 400
    
    try:
        conn = sqlite3.connect(db.db_path)
        
        # Összes adat lekérése
        participants = pd.read_sql_query('SELECT * FROM participants', conn)
        interactions = pd.read_sql_query('SELECT * FROM interactions', conn)
        questionnaire = pd.read_sql_query('SELECT * FROM questionnaire', conn)
        
        conn.close()
        
        if format == 'csv':
            # CSV exportálás
            timestamp = datetime.datetime.now().strftime('%Y%m%d_%H%M%S')
            
            participants.to_csv(f'results/participants_{timestamp}.csv', index=False)
            interactions.to_csv(f'results/interactions_{timestamp}.csv', index=False)
            questionnaire.to_csv(f'results/questionnaire_{timestamp}.csv', index=False)
            
            return f"Data exported to results/ folder with timestamp {timestamp}"
        
        else:  # json
            data = {
                'participants': participants.to_dict('records'),
                'interactions': interactions.to_dict('records'),
                'questionnaire': questionnaire.to_dict('records'),
                'export_timestamp': datetime.datetime.now().isoformat()
            }
            return jsonify(data)
    
    except Exception as e:
        return f"Export error: {e}", 500

if __name__ == '__main__':
    # Development szerver
    port = int(os.environ.get('PORT', 5000))
    debug = os.environ.get('FLASK_ENV') != 'production'
    app.run(host='0.0.0.0', port=port, debug=debug)
