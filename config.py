import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    # Configuration de base
    SECRET_KEY = os.getenv('SECRET_KEY', 'votre_clé_secrète_complexe_ici')
    
    # Configuration PostgreSQL
    POSTGRES_LOCAL = {
        "host": os.getenv('POSTGRES_HOST', 'localhost'),
        "database": os.getenv('POSTGRES_DB', 'pharmadatabase'),
        "user": os.getenv('POSTGRES_USER', 'postgres'),
        "password": os.getenv('POSTGRES_PASSWORD', 'Elisha10'),
        "port": os.getenv('POSTGRES_PORT', '5432')
    }
    
    # Configuration Render (externe)
    POSTGRES_RENDER = {
        "host": "dpg-d1lerhje5dus73fkkk6g-a",
        "database": "pharmadatabase",
        "user": "pharmadatabase_user",
        "password": "WQSRXZWsY2KYpxQAdmqENzqcvRrzpX7K",
        "port": "5432"  # Port par défaut pour PostgreSQL
    }
    
    # Configuration SQLAlchemy (choix automatique selon l'environnement)
    @property
    def SQLALCHEMY_DATABASE_URI(self):
        if os.getenv('FLASK_ENV') == 'production':
            return f"postgresql://{self.POSTGRES_RENDER['user']}:{self.POSTGRES_RENDER['password']}@{self.POSTGRES_RENDER['host']}:{self.POSTGRES_RENDER['port']}/{self.POSTGRES_RENDER['database']}"
        return f"postgresql://{self.POSTGRES_LOCAL['user']}:{self.POSTGRES_LOCAL['password']}@{self.POSTGRES_LOCAL['host']}:{self.POSTGRES_LOCAL['port']}/{self.POSTGRES_LOCAL['database']}"
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # Options du moteur
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
    def check_db_connection(cls, render=False):
        """Vérifie la connexion à la base de données"""
        try:
            import psycopg2
            config = cls.POSTGRES_RENDER if render else cls.POSTGRES_LOCAL
            conn = psycopg2.connect(**config)
            conn.close()
            return True, f"Connexion {'Render' if render else 'locale'} réussie"
        except Exception as e:
            return False, f"Erreur de connexion {'Render' if render else 'locale'}: {str(e)}"

    @classmethod
    def get_db_config(cls, render=False):
        """Retourne la configuration DB pour les scripts psycopg2"""
        return cls.POSTGRES_RENDER if render else cls.POSTGRES_LOCAL