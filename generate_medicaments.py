# generate_medicaments.py
from datetime import datetime, timedelta
from faker import Faker
from pharmaweb import create_app
from pharmaweb.models import db, Medicament, Fournisseur
import random
import sys

# Initialisation
fake = Faker('fr_FR')  # Utilisation du français pour des données plus réalistes
print('Déja le debut ...5%')
# Configuration des données
CATEGORIES = [
    "Antibiotiques", "Antidouleurs", "Antihistaminiques", "Antiviraux",
    "Antifongiques", "Antidiabétiques", "Antihypertenseurs", "Anti-inflammatoires",
    "Antidépresseurs", "Vitamines", "Cardiovasculaires", "Gastro-intestinaux",
    "Respiratoires", "Dermatologiques", "Ophtalmiques", "Pédiatriques",
    "Gynécologiques", "Neurologiques", "Oncologiques", "Homéopathiques"
]

FORMES_GALENIQUES = [
    "Comprimé", "Gélule", "Sirop", "Injectable",
    "Pommade", "Crème", "Suppositoire", "Collyre",
    "Spray", "Patch"
]

DOSAGES = ["50mg", "100mg", "200mg", "250mg", "500mg", "1g", "5mg/ml", "10mg/ml", "20mg/ml", "2%"]

def create_fournisseurs():
    """Crée des fournisseurs initiaux si nécessaire"""
    if Fournisseur.query.count() == 0:
        fournisseurs = [
            Fournisseur(
                nom="PharmaCongo",
                contact=fake.name(),
                telephone=fake.phone_number(),
                email=fake.email(),
                adresse=fake.address(),
                actif=True
            ),
            Fournisseur(
                nom="MediKinshasa",
                contact=fake.name(),
                telephone=fake.phone_number(),
                email=fake.email(),
                adresse=fake.address(),
                actif=True
            ),
            Fournisseur(
                nom="BioPharma RDC",
                contact=fake.name(),
                telephone=fake.phone_number(),
                email=fake.email(),
                adresse=fake.address(),
                actif=True
            )
        ]
        db.session.add_all(fournisseurs)
        db.session.commit()
        print(f"✅ {len(fournisseurs)} fournisseurs créés")
    return Fournisseur.query.all()
print('avant la generation des produits... 30%')
def generate_medicaments(nombre=20):
    """Génère des médicaments de test"""
    fournisseurs = create_fournisseurs()
    medicaments = []
    
    for _ in range(nombre):
        prix_achat = random.randint(500, 5000)
        marge = random.uniform(1.2, 2.0)
        
        medicament = Medicament(
            code_cip=f"CIP-{fake.unique.bothify(text='####-####')}",
            nom_commercial=f"{fake.unique.last_name()} {random.choice(['Pharma', 'Med', 'Life', 'Care'])}",
            dci=fake.last_name().upper(),
            forme_galenique=random.choice(FORMES_GALENIQUES),
            dosage=random.choice(DOSAGES),
            categorie=random.choice(CATEGORIES),
            stock_actuel=random.randint(10, 200),
            stock_minimum=random.randint(5, 20),
            prix_achat=prix_achat,
            prix_vente=round(prix_achat * marge, 2),
            tva=random.choice([0, 5, 16, 18]),
            remboursable=random.choice([True, False]),
            conditionnement=f"Boîte de {random.randint(1, 100)} {random.choice(['comprimés', 'gélules'])}",
            date_peremption=datetime.now() + timedelta(days=random.randint(30, 365*3)),
            fournisseur_id=random.choice(fournisseurs).id
        )
        medicaments.append(medicament)
    print("100%")
    try:
        db.session.add_all(medicaments)
        db.session.commit()
        print(f"✅ {len(medicaments)} médicaments générés avec succès")
        return True
    except Exception as e:
        db.session.rollback()
        print(f"❌ Erreur lors de l'insertion: {str(e)}")
        return False

def verify_data():
    """Vérifie les données dans la base"""
    print("\n🔍 Vérification des données:")
    print(f"Fournisseurs: {Fournisseur.query.count()}")
    print(f"Médicaments: {Medicament.query.count()}")
    
    if Medicament.query.count() > 0:
        print("\nExemple de médicament:")
        med = Medicament.query.first()
        print(f"Nom: {med.nom_commercial}")
        print(f"CIP: {med.code_cip}")
        print(f"Stock: {med.stock_actuel}")

if __name__ == "__main__":
    # Initialisation de l'app Flask
    app = create_app()
    
    with app.app_context():
        print("⚡ Début du script de génération de données")
        
        # Test de connexion
        try:
            db.engine.connect()
            print("✅ Connexion à la base établie")
        except Exception as e:
            print(f"❌ Impossible de se connecter à la base: {str(e)}")
            sys.exit(1)
        
        # Génération des données
        success = generate_medicaments()
        
        # Vérification
        if success:
            verify_data()