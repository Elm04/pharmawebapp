from pharmaweb import create_app, db
from pharmaweb.models import Utilisateur

app = create_app()

with app.app_context():
    # Importer la fonction d'initialisation
    from pharmaweb import initialize_database
    initialize_database()
    print("Base de données initialisée avec succès!")
    print("Utilisateurs créés :")
    print("- Admin: login=admin / motdepasse=e n")
    print("- Caissier: login=caissier / motdepasse=caissier123")