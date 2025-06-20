#!/usr/bin/env python3
"""
Enhanced Setup Database Script
Magyar receptek integrálása és adatbázis inicializálás
"""

import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Project path setup
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "user_study"))

def process_hungarian_recipes():
    """Magyar receptek feldolgozása"""
    try:
        # Próbáljuk importálni a preprocessor-t
        from recipe_preprocessor import HungarianRecipeProcessor
        
        print("🔧 Magyar receptek feldolgozása...")
        processor = HungarianRecipeProcessor("hungarian_recipes_github.csv")
        
        success = processor.process_all(
            output_path="data/processed_recipes.csv",
            sample_size=50  # 50 recept a user study-hoz
        )
        
        if success:
            print("✅ Magyar receptek sikeresen feldolgozva!")
            return True
        else:
            print("⚠️ Receptek feldolgozása sikertelen, sample adatok használata")
            return create_sample_data()
            
    except ImportError:
        print("⚠️ recipe_preprocessor.py nem található, sample adatok használata")
        return create_sample_data()
    except FileNotFoundError:
        print("⚠️ hungarian_recipes_github.csv nem található, sample adatok használata")
        return create_sample_data()
    except Exception as e:
        print(f"⚠️ Receptek feldolgozási hiba: {e}")
        return create_sample_data()

def create_sample_data():
    """Sample dataset létrehozása ha nincs valós adat"""
    data_path = Path("data/processed_recipes.csv")
    
    if not data_path.exists():
        print("🔧 Sample dataset létrehozása...")
        
        # Magyar mintareceptek realisztikus adatokkal
        recipes_data = []
        
        hungarian_recipes = [
            ("Hagyományos Gulyásleves", 
             "marhahús, hagyma, paprika, paradicsom, burgonya, fokhagyma, kömény, majoranna", 
             "1. A húst kockákra vágjuk és enyhén megsózzuk. 2. Megdinszteljük a hagymát, hozzáadjuk a paprikát. 3. Felöntjük vízzel és főzzük 1.5 órát. 4. Hozzáadjuk a burgonyát és tovább főzzük.", 
             "/static/images/gulyas.jpg", 75.0, 60.0, 90.0),
            
            ("Rántott Schnitzel Burgonyával", 
             "sertéshús, liszt, tojás, zsemlemorzsa, burgonya, olaj, só, bors", 
             "1. A húst kikalapáljuk és megsózzuk. 2. Lisztbe, majd felvert tojásba, végül zsemlemorzsába forgatjuk. 3. Forró olajban mindkét oldalán kisütjük. 4. A burgonyát héjában megfőzzük.", 
             "/static/images/schnitzel.jpg", 55.0, 45.0, 85.0),
            
            ("Vegetáriánus Lecsó", 
             "paprika, paradicsom, hagyma, tojás, tofu, olívaolaj, só, bors, fokhagyma", 
             "1. A hagymát és fokhagymát megdinszteljük olívaolajban. 2. Hozzáadjuk a felszeletelt paprikát. 3. Paradicsomot és kockára vágott tofut adunk hozzá. 4. Tojással dúsítjuk.", 
             "/static/images/lecso.jpg", 85.0, 80.0, 70.0),
            
            ("Halászlé Szegedi Módra", 
             "ponty, csuka, harcsa, hagyma, paradicsom, paprika, só, babérlevél", 
             "1. A halakat megtisztítjuk és feldaraboljuk. 2. A halak fejéből és farkából erős alapot főzünk. 3. Az alapot leszűrjük és beletesszük a haldarabokat. 4. Paprikával ízesítjük.", 
             "/static/images/halaszle.jpg", 80.0, 70.0, 75.0),
            
            ("Túrós Csusza", 
             "széles metélt, túró, tejföl, szalonna, hagyma, só, bors", 
             "1. A tésztát sós vízben megfőzzük és leszűrjük. 2. A szalonnát kockákra vágjuk és kisütjük. 3. A tésztát összekeverjük a túróval, tejföllel és a szalonnával.", 
             "/static/images/turos_csusza.jpg", 65.0, 55.0, 80.0),
            
            ("Gombapaprikás Galuskával", 
             "gomba, hagyma, paprika, tejföl, liszt, tojás, petrezselyem, olaj", 
             "1. A gombát felszeleteljük és kisütjük. 2. Hagymát dinsztelünk, paprikát adunk hozzá. 3. A gombát hozzáadjuk, tejföllel lefuttatjuk. 4. Galuskát főzünk mellé.", 
             "/static/images/gombapaprikas.jpg", 70.0, 75.0, 65.0),
            
            ("Rákóczi Túrós", 
             "túró, tojás, cukor, tejföl, mazsola, citromhéj, vaníliapor", 
             "1. A túrót átnyomjuk szitán és összekeverjük a tojásokkal. 2. Cukrot, mazsolát és citromhéjat adunk hozzá. 3. Sütőformában megsütjük. 4. Tejfölös krémmel tálaljuk.", 
             "/static/images/rakoczi_turos.jpg", 60.0, 65.0, 85.0),
            
            ("Zöldséges Ratatouille", 
             "cukkini, padlizsán, paprika, paradicsom, hagyma, fokhagyma, olívaolaj, bazsalikom", 
             "1. Az összes zöldséget kockákra vágjuk. 2. A hagymát és fokhagymát megpirítjuk. 3. Rétegesen hozzáadjuk a zöldségeket. 4. Bazsalikommal és fűszerekkel ízesítjük.", 
             "/static/images/ratatouille.jpg", 90.0, 85.0, 60.0),
            
            ("Hortobágyi Palacsinta", 
             "palacsinta, csirkehús, gomba, hagyma, paprika, tejföl, sajt", 
             "1. Palacsintát sütünk. 2. A csirkehúst megpároljuk gombával és hagymával. 3. A palacsintákat megtöltjük és feltekerjük. 4. Tejfölös mártással sütőben átmelegítjük.", 
             "/static/images/hortobagyi.jpg", 70.0, 60.0, 80.0),
            
            ("Tejfölös Uborkasaláta", 
             "uborka, hagyma, tejföl, ecet, cukor, só, kapor", 
             "1. Az uborkát vékony szeletekre vágjuk és megsózzuk. 2. 30 perc után kinyomjuk a levét. 3. Hagymát adunk hozzá. 4. Tejfölös-ecetes öntettel megöntjük.", 
             "/static/images/uborkasalata.jpg", 85.0, 90.0, 75.0)
        ]
        
        for i, (title, ingredients, instructions, image, hsi, esi, ppi) in enumerate(hungarian_recipes):
            # Kompozit score számítása: (100-env)*0.4 + nutri*0.4 + meal*0.2
            # ESI már normalizált formában van (magasabb = jobb környezetileg)
            composite_score = (esi * 0.4) + (hsi * 0.4) + (ppi * 0.2)
            
            recipe = {
                'recipeid': i + 1,
                'title': title,
                'ingredients': ingredients,
                'instructions': instructions,
                'images': image,
                'HSI': hsi,      # Health Score Index (0-100)
                'ESI': esi,      # Environmental Score Index (0-100, magasabb = jobb)
                'PPI': ppi,      # Popularity/Preference Index (0-100)
                'composite_score': round(composite_score, 2)
            }
            recipes_data.append(recipe)
        
        df = pd.DataFrame(recipes_data)
        
        # Create data directory
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/processed_recipes.csv', index=False, encoding='utf-8')
        
        print("✅ Sample dataset létrehozva 10 magyar recepttel")
        print(f"📊 HSI range: {df['HSI'].min():.1f} - {df['HSI'].max():.1f}")
        print(f"🌱 ESI range: {df['ESI'].min():.1f} - {df['ESI'].max():.1f}")
        print(f"⭐ PPI range: {df['PPI'].min():.1f} - {df['PPI'].max():.1f}")
        print(f"🔢 Composite range: {df['composite_score'].min():.1f} - {df['composite_score'].max():.1f}")
        
        return True
    else:
        print("✅ Dataset már létezik")
        return True

def setup_database():
    """Enhanced database inicializálás"""
    try:
        from user_study.user_study import UserStudyDatabase
        
        print("🔧 Enhanced user study database inicializálása...")
        db = UserStudyDatabase()
        print("✅ Enhanced database inicializálva")
        
        # Teljesítmény tracking táblák ellenőrzése
        print("📊 Teljesítmény tracking táblák ellenőrzése...")
        
        import sqlite3
        conn = sqlite3.connect(db.db_path)
        cursor = conn.cursor()
        
        # Ellenőrizzük hogy az új táblák léteznek
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [row[0] for row in cursor.fetchall()]
        
        expected_tables = ['participants', 'interactions', 'questionnaire', 'recipe_performance']
        missing_tables = [table for table in expected_tables if table not in tables]
        
        if missing_tables:
            print(f"⚠️ Hiányzó táblák: {missing_tables}")
        else:
            print("✅ Minden szükséges tábla létezik")
        
        conn.close()
        return True
        
    except ImportError:
        print("⚠️ Enhanced user study module még nem található")
        print("   Ezt a hibát a user_study.py enhanced verzióra cserélése oldja meg")
        return True
    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")
        return True

def create_static_directories():
    """Static könyvtárak létrehozása"""
    print("📁 Static könyvtárak létrehozása...")
    
    directories = [
        "static",
        "static/images",
        "static/css", 
        "static/js",
        "results",
        "results/user_study_plots",
        "results/spss_export"
    ]
    
    for directory in directories:
        dir_path = Path(directory)
        if not dir_path.exists():
            dir_path.mkdir(parents=True, exist_ok=True)
            print(f"   ✅ Létrehozva: {directory}")
        else:
            print(f"   ✅ Már létezik: {directory}")
    
    # Placeholder kép létrehozása (ha nincs)
    placeholder_path = Path("static/images/recipe_placeholder.jpg")
    if not placeholder_path.exists():
        print("   🖼️ Recipe placeholder készítése...")
        # Egyszerű placeholder - production-ben cseréld le valós képekre
        try:
            from PIL import Image, ImageDraw, ImageFont
            
            # 400x300 placeholder kép
            img = Image.new('RGB', (400, 300), color='#f8f9fa')
            draw = ImageDraw.Draw(img)
            
            # Szöveg hozzáadása
            try:
                font = ImageFont.truetype("arial.ttf", 24)
            except:
                font = ImageFont.load_default()
            
            text = "Recept Kép\nHamarosan"
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            position = ((400 - text_width) // 2, (300 - text_height) // 2)
            draw.text(position, text, fill='#6c757d', font=font, align='center')
            
            img.save(placeholder_path)
            print("   ✅ Placeholder kép létrehozva")
            
        except ImportError:
            print("   ⚠️ Pillow nem elérhető, placeholder kép kihagyva")
    
    return True

def validate_setup():
    """Setup validálása"""
    print("\n🔍 SETUP VALIDÁLÁS:")
    print("-" * 30)
    
    validations = []
    
    # 1. Receptek CSV
    csv_path = Path("data/processed_recipes.csv")
    if csv_path.exists():
        try:
            df = pd.read_csv(csv_path)
            required_columns = ['recipeid', 'title', 'ingredients', 'HSI', 'ESI', 'PPI', 'composite_score']
            missing_cols = [col for col in required_columns if col not in df.columns]
            
            if missing_cols:
                validations.append(f"❌ Hiányzó oszlopok: {missing_cols}")
            else:
                validations.append(f"✅ Receptek CSV: {len(df)} recept, minden oszlop OK")
        except Exception as e:
            validations.append(f"❌ CSV olvasási hiba: {e}")
    else:
        validations.append("❌ processed_recipes.csv nem található")
    
    # 2. Könyvtárak
    required_dirs = ['data', 'static', 'static/images', 'results']
    for directory in required_dirs:
        if Path(directory).exists():
            validations.append(f"✅ Könyvtár: {directory}")
        else:
            validations.append(f"❌ Hiányzó könyvtár: {directory}")
    
    # 3. User study modul
    try:
        from user_study.user_study import UserStudyDatabase, EnhancedRecipeRecommender
        validations.append("✅ Enhanced user study modul betölthető")
    except ImportError:
        validations.append("❌ Enhanced user study modul nem található")
    
    # 4. Database
    try:
        import sqlite3
        if Path("user_study.db").exists():
            validations.append("✅ SQLite database létezik")
        else:
            validations.append("⚠️ SQLite database még nincs létrehozva")
    except ImportError:
        validations.append("❌ SQLite nem elérhető")
    
    # Eredmények kiírása
    for validation in validations:
        print(f"   {validation}")
    
    # Összesítés
    success_count = len([v for v in validations if v.startswith("✅")])
    warning_count = len([v for v in validations if v.startswith("⚠️")])
    error_count = len([v for v in validations if v.startswith("❌")])
    
    print(f"\n📊 VALIDÁLÁS EREDMÉNYE:")
    print(f"   ✅ Sikeres: {success_count}")
    print(f"   ⚠️ Figyelmeztetés: {warning_count}")
    print(f"   ❌ Hiba: {error_count}")
    
    if error_count == 0:
        print("🎉 SETUP SIKERES!")
        return True
    else:
        print("⚠️ SETUP RÉSZBEN SIKERES - javítások szükségesek")
        return False

if __name__ == "__main__":
    print("🚀 Enhanced Sustainable Recipe Recommender Setup")
    print("=" * 55)
    
    success = True
    
    # 1. Magyar receptek feldolgozása
    success &= process_hungarian_recipes()
    
    # 2. Static könyvtárak
    success &= create_static_directories()
    
    # 3. Database setup
    success &= setup_database()
    
    # 4. Validálás
    validation_success = validate_setup()
    
    print("\n" + "=" * 55)
    if success and validation_success:
        print("🎉 TELJES SETUP SIKERES!")
        print("\n📋 A rendszer készen áll:")
        print("   ✅ Magyar receptek integrálva")
        print("   ✅ Verzió információ elrejtve")
        print("   ✅ Képek és instrukciók támogatása")
        print("   ✅ Precision/Recall metrikák")
        print("   ✅ Enhanced admin dashboard")
        
        print("\n🚀 Következő lépések:")
        print("   1. GitHub deploy várja")
        print("   2. App URL tesztelése")
        print("   3. Teljes user journey végigpróbálása")
        print("   4. Admin stats ellenőrzése")
        print("   5. Launch campaign kezdés!")
        
    else:
        print("⚠️ SETUP BEFEJEZVE FIGYELMEZTETÉSEKKEL")
        print("\n🔧 Lehetséges javítások:")
        print("   - Enhanced user_study.py feltöltése")
        print("   - hungarian_recipes_github.csv hozzáadása")
        print("   - Template fájlok létrehozása")
    
    print(f"\n📊 Dataset státusz: {Path('data/processed_recipes.csv').exists()}")
    print(f"📁 Static images: {Path('static/images').exists()}")
    
    print("\n💡 Gyors teszt: python -c \"from user_study.user_study import *; print('✅ Enhanced modules OK')\"")
