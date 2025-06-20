import os
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# Project path setup
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))
sys.path.insert(0, str(project_root / "user_study"))

def create_sample_data():
    """Sample dataset létrehozása ha nem létezik"""
    
    data_path = Path("data/processed_recipes.csv")
    
    if not data_path.exists():
        print("🔧 Creating sample dataset...")
        
        # Sample recipes with various characteristics
        recipes_data = []
        
        for i in range(1, 101):
            recipe = {
                'recipeid': i,
                'title': f'Delicious Recipe {i}',
                'ingredients': [
                    'tomatoes, garlic, olive oil, basil, onion',
                    'chicken breast, rice, mixed vegetables, herbs',
                    'pasta, parmesan cheese, cream, black pepper',
                    'salmon fillet, lemon, dill, asparagus',
                    'black beans, corn, bell peppers, avocado, lime',
                    'quinoa, roasted vegetables, feta cheese, herbs',
                    'ground turkey, sweet potato, spinach, garlic',
                    'tofu, broccoli, soy sauce, ginger, sesame oil',
                    'lentils, carrots, celery, vegetable broth',
                    'eggs, spinach, mushrooms, cheese'
                ][i % 10],
                'HSI': round(np.random.uniform(0.2, 0.9), 3),  # Health Score
                'ESI': round(np.random.uniform(0.1, 0.8), 3),  # Environmental Score  
                'PPI': round(np.random.uniform(0.3, 1.0), 3)   # Popularity Score
            }
            recipes_data.append(recipe)
        
        df = pd.DataFrame(recipes_data)
        
        # Create data directory
        os.makedirs('data', exist_ok=True)
        df.to_csv('data/processed_recipes.csv', index=False)
        
        print("✅ Sample dataset created with 100 recipes")
        print(f"📊 HSI range: {df['HSI'].min():.2f} - {df['HSI'].max():.2f}")
        print(f"🌱 ESI range: {df['ESI'].min():.2f} - {df['ESI'].max():.2f}")
        return True
    else:
        print("✅ Dataset already exists")
        return True

def setup_database():
    """Database inicializálás"""
    
    try:
        from user_study.user_study import UserStudyDatabase
        
        print("🔧 Initializing user study database...")
        db = UserStudyDatabase()
        print("✅ Database initialized successfully")
        return True
        
    except ImportError:
        print("⚠️ User study module not found - will be created later")
        return True
    except Exception as e:
        print(f"⚠️ Database setup warning: {e}")
        return True

if __name__ == "__main__":
    print("🚀 Setting up Sustainable Recipe Recommender...")
    print("=" * 50)
    
    success = True
    success &= create_sample_data()
    success &= setup_database()
    
    print("=" * 50)
    if success:
        print("🎉 Setup completed successfully!")
    else:
        print("⚠️ Setup completed with warnings")
    
    print("\n📋 Next steps:")
    print("1. Add user study files")  
    print("2. Configure Heroku deployment")
    print("3. Set up environment secrets")
