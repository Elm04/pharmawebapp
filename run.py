from pharmaweb import mainapp
from pharmaweb.models import db
from config import Config

# Crée l'application en mode production
app = mainapp(Config)  # Passez toujours la config

# Initialisation de la base de données
with app.app_context():
    db.create_all()
    # Importez et initialisez les données si nécessaire
    from pharmaweb.models import Utilisateur, ParametrePharmacie
    if not ParametrePharmacie.query.first():
        db.session.add(ParametrePharmacie())
        db.session.commit()

if __name__ == "__main__":
    app.run()