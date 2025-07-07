from config import Config
from sqlalchemy import create_engine

engine = create_engine(Config.SQLALCHEMY_DATABASE_URI)
try:
    with engine.connect() as conn:
        print("✅ Connexion SQLite réussie!")
        print(f"Base de données créée : {Config.SQLALCHEMY_DATABASE_URI}")
except Exception as e:
    print(f"❌ Erreur : {e}")
    print("Vérifiez que :")
    print(f"1. Le dossier 'instance' existe : {Config.INSTANCE_DIR}")
    print("2. L'application a les droits d'écriture")