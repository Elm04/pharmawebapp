import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuration de base
    SECRET_KEY = os.getenv('SECRET_KEY')
    
    # Configuration PostgreSQL - Version corrigée
    @staticmethod
    def get_database_uri():
        database_url = os.getenv('DATABASE_URL', '')
        if not database_url:
            raise ValueError("DATABASE_URL must be set in environment variables")
        
        # Correction pour Render
        if database_url.startswith('postgres://'):
            database_url = database_url.replace('postgres://', 'postgresql://', 1)
        
        return database_url
    
    # Doit être une chaîne, pas une propriété
    SQLALCHEMY_DATABASE_URI = get_database_uri.__func__()  # Appel immédiat
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'pool_size': 5,
        'pool_timeout': 30,
        'max_overflow': 10,
        'connect_args': {
            'connect_timeout': 5,
            'sslmode': 'require' if os.getenv('FLASK_ENV') == 'production' else None
        }
    }

    @classmethod
    def check_db_connection(cls):
        """Vérifie la connexion à la base de données"""
        try:
            import psycopg2
            conn = psycopg2.connect(cls.SQLALCHEMY_DATABASE_URI, connect_timeout=5)
            conn.close()
            return True, "Connexion réussie"
        except Exception as e:
            return False, f"Erreur de connexion: {str(e)}"