import os
from dotenv import load_dotenv
from pathlib import Path

load_dotenv()

BASE_DIR = Path(__file__).parent.parent
INSTANCE_DIR = BASE_DIR / 'instance'
INSTANCE_DIR.mkdir(exist_ok=True)  # Crée le dossier si inexistant

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY', 'default-secret-key')
    
    # Chemin absolu pour SQLite
    SQLALCHEMY_DATABASE_URI = f"sqlite:///{INSTANCE_DIR / 'pharma.db'}"
    
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_pre_ping': True,
        'connect_args': {'check_same_thread': False}
    }
    
    SQLALCHEMY_TRACK_MODIFICATIONS = False