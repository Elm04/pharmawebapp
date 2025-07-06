import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv('SECRET_KEY') or 'une-cle-secrete-tres-secure'
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URL') or 'sqlite:///pharma.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16MB max upload size
    
    
    # Paramètres pour les rôles
    ROLES = {
        'admin': 'Administrateur',
        'pharmacien': 'Pharmacien',
        'caissier': 'Caissier',
        'preparateur': 'Préparateur'
    }
    
    # Configuration pour les uploads
    UPLOAD_FOLDER = 'static/uploads/medicaments'
    ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}
    # Ajoutez cette configuration
    NOM_PHARMACIE = "Ma Pharmacie"