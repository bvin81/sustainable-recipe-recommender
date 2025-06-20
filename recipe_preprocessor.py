#!/usr/bin/env python3
"""
Magyar receptek adatfeldolgozása és normalizálása
Valós hungarian_recipes_github.csv integrálása a user study rendszerbe
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys

class HungarianRecipeProcessor:
    """Magyar receptek feldolgozása és normalizálása"""
    
    def __init__(self, csv_file_path="hungarian_recipes_github.csv"):
        self.csv_path = csv_file_path
        self.processed_data = None
        
    def load_and_validate_data(self):
        """CSV betöltése és validálása"""
        try:
            print(f"📊 Betöltés: {self.csv_path}")
            df = pd.read_csv(self.csv_path, encoding='utf-8')
            
            print(f"✅ Sikeresen betöltve: {len(df)} recept")
            print(f"📋 Oszlopok: {list(df.columns)}")
            
            # Kötelező oszlopok ellenőrzése
            required_columns = ['name', 'ingredients', 'instructions', 'images', 
                              'env_score', 'nutri_score', 'meal_score']
            
            missing_columns = [col for col in required_columns if col not in df.columns]
            if missing_columns:
                print(f"⚠️ Hiányzó oszlopok: {missing_columns}")
                return None
            
            return df
            
        except FileNotFoundError:
            print(f"❌ Fájl nem található: {self.csv_path}")
            return None
        except Exception as e:
            print(f"❌ Hiba a betöltés során: {e}")
            return None
    
    def normalize_env_score(self, df):
        """
        Környezeti pontszám normalizálása 0-100 skálára
        Magasabb env_score = nagyobb környezeti terhelés → alacsonyabb normalizált érték
        """
        print("🌱 Környezeti pontszámok normalizálása...")
        
        # Eredeti tartomány
        env_min = df['env_score'].min()
        env_max = df['env_score'].max()
        print(f"   Eredeti env_score tartomány: {env_min:.2f} - {env_max:.2f}")
        
        # Min-Max normalizálás 0-100-ra, majd invertálás
        # Magas eredeti érték → alacsony normalizált érték (rossz környezetileg)
        df['env_score_normalized'] = 100 - ((df['env_score'] - env_min) / (env_max - env_min)) * 100
        
        # Ellenőrzés
        norm_min = df['env_score_normalized'].min()
        norm_max = df['env_score_normalized'].max()
        print(f"   Normalizált env_score tartomány: {norm_min:.2f} - {norm_max:.2f}")
        
        return df
    
    def calculate_composite_score(self, df):
        """
        Kompozit pontszám számítása
        comp_score = env_score_normalized * 0.4 + nutri_score * 0.4 + meal_score * 0.2
        """
        print("🔢 Kompozit pontszám számítása...")
        
        # Súlyok
        env_weight = 0.4
        nutri_weight = 0.4
        meal_weight = 0.2
        
        df['comp_score'] = (
            df['env_score_normalized'] * env_weight +
            df['nutri_score'] * nutri_weight +
            df['meal_score'] * meal_weight
        )
        
        # Statisztikák
        comp_min = df['comp_score'].min()
        comp_max = df['comp_score'].max()
        comp_mean = df['comp_score'].mean()
        
        print(f"   Kompozit score tartomány: {comp_min:.2f} - {comp_max:.2f}")
        print(f"   Átlagos kompozit score: {comp_mean:.2f}")
        
        return df
    
    def clean_and_prepare_data(self, df):
        """Adatok tisztítása és előkészítése a user study-hoz"""
        print("🧹 Adatok tisztítása...")
        
        # Hiányzó értékek kezelése
        df = df.dropna(subset=['name', 'ingredients'])
        
        # Üres képek helyettesítése placeholder-rel
        df['images'] = df['images'].fillna('/static/images/recipe_placeholder.jpg')
        
        # Üres instrukciók helyettesítése
        df['instructions'] = df['instructions'].fillna('Részletes elkészítési útmutató hamarosan.')
        
        # Szöveges mezők tisztítása
        df['name'] = df['name'].str.strip()
        df['ingredients'] = df['ingredients'].str.strip()
        df['instructions'] = df['instructions'].str.strip()
        
        # User study kompatibilis oszlopnevekkel
        df_clean = df.rename(columns={
            'name': 'title',
            'env_score_normalized': 'ESI',  # Environmental Score Index
            'nutri_score': 'HSI',           # Health Score Index  
            'meal_score': 'PPI',            # Popularity/Preference Index
            'comp_score': 'composite_score'
        })
        
        # Recipe ID hozzáadása
        df_clean['recipeid'] = range(1, len(df_clean) + 1)
        
        # Összetevők rövidítése ha túl hosszú (UI miatt)
        df_clean['ingredients_short'] = df_clean['ingredients'].apply(
            lambda x: x[:200] + '...' if len(str(x)) > 200 else x
        )
        
        print(f"✅ Tisztítva: {len(df_clean)} recept készenlétben")
        
        return df_clean
    
    def create_sample_for_user_study(self, df, sample_size=50):
        """
        Reprezentatív minta létrehozása a user study-hoz
        Különböző score tartományokból egyenletesen
        """
        print(f"🎯 User study minta létrehozása ({sample_size} recept)...")
        
        # Stratified sampling kompozit score alapján
        df['score_quartile'] = pd.qcut(df['composite_score'], q=4, labels=['low', 'medium', 'high', 'very_high'])
        
        # Egyenletes eloszlás a kvartilisek között
        samples_per_quartile = sample_size // 4
        remainder = sample_size % 4
        
        sample_dfs = []
        for i, quartile in enumerate(['low', 'medium', 'high', 'very_high']):
            quartile_df = df[df['score_quartile'] == quartile]
            
            # Maradék az első kvartiliséhez
            n_samples = samples_per_quartile + (remainder if i == 0 else 0)
            
            if len(quartile_df) >= n_samples:
                sample = quartile_df.sample(n=n_samples, random_state=42)
            else:
                sample = quartile_df  # Ha kevesebb van, mind
            
            sample_dfs.append(sample)
            print(f"   {quartile}: {len(sample)} recept")
        
        user_study_sample = pd.concat(sample_dfs, ignore_index=True)
        
        # Keverjük meg
        user_study_sample = user_study_sample.sample(frac=1, random_state=42).reset_index(drop=True)
        
        # Recipe ID újraszámozása
        user_study_sample['recipeid'] = range(1, len(user_study_sample) + 1)
        
        print(f"✅ User study minta kész: {len(user_study_sample)} recept")
        
        return user_study_sample
    
    def generate_statistics_report(self, df):
        """Statisztikai riport az adatokról"""
        print("\n📊 ADATSTATISZTIKÁK")
        print("=" * 50)
        
        print(f"📈 Receptek száma: {len(df)}")
        print(f"📋 Oszlopok: {len(df.columns)}")
        
        # Score statisztikák
        for score_col in ['HSI', 'ESI', 'PPI', 'composite_score']:
            if score_col in df.columns:
                mean_val = df[score_col].mean()
                std_val = df[score_col].std()
                min_val = df[score_col].min()
                max_val = df[score_col].max()
                
                print(f"\n{score_col}:")
                print(f"   Átlag: {mean_val:.2f} ± {std_val:.2f}")
                print(f"   Tartomány: {min_val:.2f} - {max_val:.2f}")
        
        # Top 5 recept kompozit score alapján
        if 'composite_score' in df.columns:
            print(f"\n🏆 TOP 5 RECEPT (kompozit score):")
            top_recipes = df.nlargest(5, 'composite_score')[['title', 'composite_score', 'HSI', 'ESI', 'PPI']]
            for idx, row in top_recipes.iterrows():
                print(f"   {row['title'][:40]:<40} | Score: {row['composite_score']:.1f}")
        
        # Adatminőség ellenőrzés
        print(f"\n🔍 ADATMINŐSÉG:")
        print(f"   Hiányzó címek: {df['title'].isna().sum()}")
        print(f"   Hiányzó összetevők: {df['ingredients'].isna().sum()}")
        print(f"   Hiányzó instrukciók: {df['instructions'].isna().sum()}")
        print(f"   Hiányzó képek: {df['images'].isna().sum()}")
    
    def process_all(self, output_path="data/processed_recipes.csv", sample_size=50):
        """Teljes feldolgozási pipeline"""
        print("🚀 MAGYAR RECEPTEK FELDOLGOZÁSA")
        print("=" * 50)
        
        # 1. Betöltés
        df = self.load_and_validate_data()
        if df is None:
            return False
        
        # 2. Normalizálás
        df = self.normalize_env_score(df)
        
        # 3. Kompozit score
        df = self.calculate_composite_score(df)
        
        # 4. Tisztítás
        df = self.clean_and_prepare_data(df)
        
        # 5. User study minta
        if sample_size > 0:
            df_sample = self.create_sample_for_user_study(df, sample_size)
            self.processed_data = df_sample
        else:
            self.processed_data = df
        
        # 6. Statisztikák
        self.generate_statistics_report(self.processed_data)
        
        # 7. Mentés
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.processed_data.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"\n💾 Feldolgozott adatok mentve: {output_path}")
        print(f"📁 Fájlméret: {os.path.getsize(output_path) / 1024:.1f} KB")
        
        return True

def main():
    """Fő feldolgozási script"""
    processor = HungarianRecipeProcessor("hungarian_recipes_github.csv")
    
    # Teljes feldolgozás 50 recepttel a user study-hoz
    success = processor.process_all(
        output_path="data/processed_recipes.csv",
        sample_size=50  # Optimális méret a user study-hoz
    )
    
    if success:
        print("\n🎉 FELDOLGOZÁS SIKERES!")
        print("\n📋 Következő lépések:")
        print("1. Töltsd fel a 'hungarian_recipes_github.csv' fájlt a GitHub repository-ba")
        print("2. Futtasd ezt a scriptet a setup_database.py-ban")
        print("3. A user study automatikusan használni fogja a valós recepteket")
        print("4. Precision/Recall/F1 metrikák számítása implementálásra kerül")
    else:
        print("\n❌ FELDOLGOZÁS SIKERTELEN!")
        print("Ellenőrizd a 'hungarian_recipes_github.csv' fájl elérhetőségét.")

if __name__ == "__main__":
    main()
