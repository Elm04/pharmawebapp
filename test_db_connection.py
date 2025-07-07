import os
from pharmaweb import create_app
from pharmaweb.models import db
from sqlalchemy import inspect

# Chargez l'application
app = create_app()

with app.app_context():
    try:
        # Testez la connexion
        db.engine.connect()
        print("✅ Connexion à la base de données réussie!")
        
        # Vérifiez si les tables existent (méthode compatible SQLAlchemy 1.4+)
        print("\nTables existantes:")
        inspector = inspect(db.engine)
        print(inspector.get_table_names())
        
    except Exception as e:
        print(f"❌ Erreur de connexion: {e}")
        raise