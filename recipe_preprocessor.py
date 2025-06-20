#!/usr/bin/env python3
"""
Magyar receptek adatfeldolgozása és normalizálása - TELJES VERZIÓ
Valós hungarian_recipes_github.csv integrálása külső kép URL-ekkel
"""

import pandas as pd
import numpy as np
from pathlib import Path
import os
import sys
import re
import json

class HungarianRecipeProcessor:
    """Magyar receptek feldolgozása és normalizálása külső képekkel"""
    
    def __init__(self, csv_file_path="hungarian_recipes_github.csv"):
        self.csv_path = csv_file_path
        self.processed_data = None
        
    def load_and_validate_data(self):
        """CSV betöltése és validálása"""
        try:
            print(f"📊 Betöltés: {self.csv_path}")
            
            # Többféle encoding próbálása
            encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
            df = None
            
            for encoding in encodings:
                try:
                    df = pd.read_csv(self.csv_path, encoding=encoding)
                    print(f"✅ Sikeres betöltés {encoding} encoding-gal")
                    break
                except UnicodeDecodeError:
                    continue
            
            if df is None:
                print("❌ Nem sikerült betölteni egyik encoding-gal sem")
                return None
            
            print(f"✅ Sikeresen betöltve: {len(df)} recept")
            print(f"📋 Oszlopok: {list(df.columns)}")
            
            # Kötelező oszlopok ellenőrzése
            required_columns = ['name', 'ingredients', 'env_score', 'nutri_score', 'meal_score']
            optional_columns = ['instructions', 'images']
            
            missing_required = [col for col in required_columns if col not in df.columns]
            if missing_required:
                print(f"❌ Hiányzó kötelező oszlopok: {missing_required}")
                return None
            
            missing_optional = [col for col in optional_columns if col not in df.columns]
            if missing_optional:
                print(f"⚠️ Hiányzó opcionális oszlopok: {missing_optional}")
                # Létrehozzuk az üres oszlopokat
                for col in missing_optional:
                    df[col] = ''
            
            # Alapvető adatminőség ellenőrzés
            print(f"🔍 Adatminőség ellenőrzés:")
            print(f"   Üres nevek: {df['name'].isna().sum()}")
            print(f"   Üres összetevők: {df['ingredients'].isna().sum()}")
            print(f"   Env_score tartomány: {df['env_score'].min():.2f} - {df['env_score'].max():.2f}")
            print(f"   Nutri_score tartomány: {df['nutri_score'].min():.2f} - {df['nutri_score'].max():.2f}")
            print(f"   Meal_score tartomány: {df['meal_score'].min():.2f} - {df['meal_score'].max():.2f}")
            
            return df
            
        except FileNotFoundError:
            print(f"❌ Fájl nem található: {self.csv_path}")
            return None
        except Exception as e:
            print(f"❌ Hiba a betöltés során: {e}")
            return None
    
    def process_image_urls(self, images_string):
        """
        Kép URL-ek feldolgozása - első valós URL kiválasztása
        Kezeli a vessző-separated URL listákat és idézőjeleket
        """
        if pd.isna(images_string) or not images_string or images_string == '':
            return self.get_placeholder_image()
        
        # String átalakítás és tisztítás
        images_str = str(images_string).strip()
        
        # Ha üres vagy csak whitespace
        if not images_str:
            return self.get_placeholder_image()
        
        try:
            # Comma-separated URLs feldolgozása
            if ',' in images_str:
                # Split by comma és mindegyik URL tisztítása
                urls = [url.strip().strip('"').strip("'") for url in images_str.split(',')]
            else:
                # Egyetlen URL
                urls = [images_str.strip().strip('"').strip("'")]
            
            # Első érvényes HTTP URL keresése
            for url in urls:
                if url and (url.startswith('http://') or url.startswith('https://')):
                    # További tisztítás - extra karakterek eltávolítása
                    cleaned_url = re.sub(r'["\s]+$', '', url)
                    print(f"   🖼️ Kép URL: {cleaned_url[:60]}...")
                    return cleaned_url
            
            # Ha nincs érvényes URL
            print(f"   ⚠️ Nincs érvényes URL: {images_str[:50]}...")
            return self.get_placeholder_image()
            
        except Exception as e:
            print(f"   ❌ Kép URL feldolgozási hiba: {e}")
            return self.get_placeholder_image()
    
    def get_placeholder_image(self):
        """Placeholder kép URL visszaadása"""
        return "https://via.placeholder.com/400x300/f8f9fa/6c757d?text=Recept+K%C3%A9p"
    
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
        
        # Outlierek kezelése (99th percentile alapján)
        env_99th = df['env_score'].quantile(0.99)
        env_1st = df['env_score'].quantile(0.01)
        
        # Clipping extrém értékekhez
        df['env_score_clipped'] = df['env_score'].clip(env_1st, env_99th)
        
        # Min-Max normalizálás 0-100-ra, majd invertálás
        # Magas eredeti érték → alacsony normalizált érték (rossz környezetileg)
        df['env_score_normalized'] = 100 - ((df['env_score_clipped'] - df['env_score_clipped'].min()) / 
                                           (df['env_score_clipped'].max() - df['env_score_clipped'].min())) * 100
        
        # Ellenőrzés
        norm_min = df['env_score_normalized'].min()
        norm_max = df['env_score_normalized'].max()
        print(f"   Normalizált env_score tartomány: {norm_min:.2f} - {norm_max:.2f}")
        
        return df
    
    def normalize_other_scores(self, df):
        """Nutri_score és meal_score normalizálása 0-100 skálára ha szükséges"""
        print("📊 Egyéb pontszámok normalizálása...")
        
        for score_col in ['nutri_score', 'meal_score']:
            col_min = df[score_col].min()
            col_max = df[score_col].max()
            
            print(f"   {score_col} tartomány: {col_min:.2f} - {col_max:.2f}")
            
            # Ha már 0-100 között van, nem kell normalizálni
            if col_min >= 0 and col_max <= 100:
                print(f"   {score_col} már normalizált")
                continue
            
            # Min-Max normalizálás 0-100-ra
            df[f'{score_col}_normalized'] = ((df[score_col] - col_min) / (col_max - col_min)) * 100
            
            # Eredeti oszlop felülírása
            df[score_col] = df[f'{score_col}_normalized']
            df.drop(f'{score_col}_normalized', axis=1, inplace=True)
            
            print(f"   {score_col} normalizálva: 0-100")
        
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
        original_count = len(df)
        df = df.dropna(subset=['name', 'ingredients'])
        cleaned_count = len(df)
        
        if original_count != cleaned_count:
            print(f"   Eltávolítva: {original_count - cleaned_count} hiányos recept")
        
        # Kép URL-ek feldolgozása
        print("🖼️ Kép URL-ek feldolgozása...")
        df['processed_images'] = df['images'].apply(self.process_image_urls)
        
        # Üres instrukciók helyettesítése
        df['instructions'] = df['instructions'].fillna('Részletes elkészítési útmutató hamarosan elérhető.')
        
        # Szöveges mezők tisztítása
        text_columns = ['name', 'ingredients', 'instructions']
        for col in text_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()
                # HTML tag-ek eltávolítása ha vannak
                df[col] = df[col].str.replace(r'<[^>]+>', '', regex=True)
                # Extra whitespace-ek eltávolítása
                df[col] = df[col].str.replace(r'\s+', ' ', regex=True)
        
        # User study kompatibilis oszlopnevekkel
        df_clean = df.rename(columns={
            'name': 'title',
            'env_score_normalized': 'ESI',  # Environmental Score Index
            'nutri_score': 'HSI',           # Health Score Index  
            'meal_score': 'PPI',            # Popularity/Preference Index
            'comp_score': 'composite_score',
            'processed_images': 'images'
        })
        
        # Recipe ID hozzáadása
        df_clean['recipeid'] = range(1, len(df_clean) + 1)
        
        # Összetevők rövidítése ha túl hosszú (UI miatt)
        df_clean['ingredients_display'] = df_clean['ingredients'].apply(
            lambda x: x[:300] + '...' if len(str(x)) > 300 else x
        )
        
        # Instrukciók rövidítése
        df_clean['instructions_display'] = df_clean['instructions'].apply(
            lambda x: x[:500] + '...' if len(str(x)) > 500 else x
        )
        
        print(f"✅ Tisztítva: {len(df_clean)} recept készenléti állapotban")
        
        return df_clean
    
    def create_sample_for_user_study(self, df, sample_size=50):
        """
        Reprezentatív minta létrehozása a user study-hoz
        Különböző score tartományokból egyenletesen
        """
        print(f"🎯 User study minta létrehozása ({sample_size} recept)...")
        
        # Ha kevesebb recept van mint a kért minta
        if len(df) <= sample_size:
            print(f"   Összes recept használva: {len(df)}")
            return df
        
        # Stratified sampling kompozit score alapján
        try:
            df['score_quartile'] = pd.qcut(df['composite_score'], q=4, labels=['low', 'medium', 'high', 'very_high'])
        except ValueError:
            # Ha nem lehet quartile-ekre osztani (túl kevés egyedi érték)
            print("   Egyszerű random sampling használata")
            return df.sample(n=sample_size, random_state=42).reset_index(drop=True)
        
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
        
        # Score quartile oszlop eltávolítása
        if 'score_quartile' in user_study_sample.columns:
            user_study_sample.drop('score_quartile', axis=1, inplace=True)
        
        print(f"✅ User study minta kész: {len(user_study_sample)} recept")
        
        return user_study_sample
    
    def generate_statistics_report(self, df):
        """Statisztikai riport az adatokról"""
        print("\n📊 ADATSTATISZTIKÁK")
        print("=" * 50)
        
        print(f"📈 Receptek száma: {len(df)}")
        print(f"📋 Oszlopok: {len(df.columns)}")
        
        # Score statisztikák
        score_columns = ['HSI', 'ESI', 'PPI', 'composite_score']
        for score_col in score_columns:
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
        print(f"   Placeholder képek: {df['images'].str.contains('placeholder').sum()}")
        print(f"   Külső képek: {df['images'].str.contains('http').sum()}")
        
        # Kép URL statisztikák
        if 'images' in df.columns:
            print(f"\n🖼️ KÉP STATISZTIKÁK:")
            total_images = len(df)
            external_images = df['images'].str.contains('http', na=False).sum()
            placeholder_images = df['images'].str.contains('placeholder', na=False).sum()
            
            print(f"   Összes recept: {total_images}")
            print(f"   Külső képek: {external_images} ({external_images/total_images*100:.1f}%)")
            print(f"   Placeholder képek: {placeholder_images} ({placeholder_images/total_images*100:.1f}%)")
    
    def process_all(self, output_path="data/processed_recipes.csv", sample_size=50):
        """Teljes feldolgozási pipeline"""
        print("🚀 MAGYAR RECEPTEK FELDOLGOZÁSA")
        print("=" * 50)
        
        # 1. Betöltés
        df = self.load_and_validate_data()
        if df is None:
            print("❌ Feldolgozás megszakítva - CSV betöltési hiba")
            return False
        
        # 2. Környezeti score normalizálás
        df = self.normalize_env_score(df)
        
        # 3. Egyéb score-ok normalizálása
        df = self.normalize_other_scores(df)
        
        # 4. Kompozit score
        df = self.calculate_composite_score(df)
        
        # 5. Tisztítás és feldolgozás
        df = self.clean_and_prepare_data(df)
        
        # 6. User study minta
        if sample_size > 0 and len(df) > sample_size:
            df_sample = self.create_sample_for_user_study(df, sample_size)
            self.processed_data = df_sample
        else:
            self.processed_data = df
        
        # 7. Statisztikák
        self.generate_statistics_report(self.processed_data)
        
        # 8. Mentés
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        self.processed_data.to_csv(output_path, index=False, encoding='utf-8')
        
        print(f"\n💾 Feldolgozott adatok mentve: {output_path}")
        print(f"📁 Fájlméret: {os.path.getsize(output_path) / 1024:.1f} KB")
        
        # 9. Mintaadatok kiírása
        print(f"\n📋 MINTA RECEPTEK:")
        for i in range(min(3, len(self.processed_data))):
            recipe = self.processed_data.iloc[i]
            print(f"   {i+1}. {recipe['title']}")
            print(f"      Kép: {recipe['images'][:60]}...")
            print(f"      Scores: HSI={recipe['HSI']:.1f}, ESI={recipe['ESI']:.1f}, PPI={recipe['PPI']:.1f}")
        
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
        print("1. A processed_recipes.csv tartalmazza a feldolgozott recepteket")
        print("2. A user study automatikusan használni fogja a valós recepteket")
        print("3. A külső képek URL-jei megjelennek a weboldalon")
        print("4. Precision/Recall/F1 metrikák számítása implementálásra kerül")
    else:
        print("\n❌ FELDOLGOZÁS SIKERTELEN!")
        print("Ellenőrizd a 'hungarian_recipes_github.csv' fájl elérhetőségét és struktúráját.")

if __name__ == "__main__":
    main()
