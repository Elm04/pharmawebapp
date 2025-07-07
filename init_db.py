from pharmaweb import mainapp, db
from pharmaweb.models import Utilisateur

app = mainapp()

with app.app_context():
    # Importer la fonction d'initialisation
    from pharmaweb import initialize_database
    initialize_database()
    print("Base de données initialisée avec succès!")
    print("Utilisateurs créés :")
    print("- Admin: login=admin / motdepasse=e n")
    print("- Caissier: login=caissier / motdepasse=caissier123")