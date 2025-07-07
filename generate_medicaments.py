# generate_medicaments.py
from datetime import datetime, timedelta
from faker import Faker
from pharmaweb.extensions import db
from pharmaweb.models import Medicament, Fournisseur
import random

fake = Faker()

# Catégories de médicaments réalistes
CATEGORIES = [
    "Antibiotiques",
    "Antidouleurs",
    "Antihistaminiques",
    "Antiviraux",
    "Antifongiques",
    "Antidiabétiques",
    "Antihypertenseurs",
    "Anti-inflammatoires",
    "Antidépresseurs",
    "Vitamines",
    "Médicaments cardiovasculaires",
    "Médicaments gastro-intestinaux",
    "Médicaments respiratoires",
    "Médicaments dermatologiques",
    "Médicaments ophtalmiques",
    "Médicaments pédiatriques",
    "Médicaments gynécologiques",
    "Médicaments neurologiques",
    "Médicaments oncologiques",
    "Médicaments homéopathiques"
]

# Formes galéniques
FORMES_GALENIQUES = [
    "Comprimé",
    "Gélule",
    "Sirop",
    "Injectable",
    "Pommade",
    "Crème",
    "Suppositoire",
    "Collyre",
    "Spray",
    "Patch"
]

# Dosages
DOSAGES = [
    "50mg",
    "100mg",
    "200mg",
    "250mg",
    "500mg",
    "1g",
    "5mg/ml",
    "10mg/ml",
    "20mg/ml",
    "2%"
]

def generate_medicaments():
    # Créer quelques fournisseurs s'ils n'existent pas
    if not Fournisseur.query.first():
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

    fournisseurs = Fournisseur.query.all()

    medicaments = []
    for i in range(1, 21):
        prix_achat = random.randint(500, 5000)  # Prix aléatoire entre 500 et 5000 CDF
        prix_vente = prix_achat * random.uniform(1.2, 2.0)  # Marge de 20% à 100%
        
        medicament = Medicament(
            code_cip=f"CIP-{fake.unique.bothify(text='####-####')}",
            nom_commercial=fake.unique.first_name() + random.choice(["", " ", "-"]) + random.choice(["Pharma", "Med", "Life", "Care", "Plus", "Fort"]),
            dci=fake.last_name().upper() + " " + random.choice(DOSAGES),
            forme_galenique=random.choice(FORMES_GALENIQUES),
            dosage=random.choice(DOSAGES),
            categorie=CATEGORIES[i-1],  # Une catégorie différente pour chaque médicament
            stock_actuel=random.randint(10, 200),
            stock_minimum=random.randint(5, 20),
            prix_achat=prix_achat,
            prix_vente=round(prix_vente, 2),
            tva=random.choice([0, 5, 16, 18]),
            remboursable=random.choice([True, False]),
            conditionnement=f"Boîte de {random.randint(1, 100)} {random.choice(['comprimés', 'gélules', 'ampoules', 'flacons'])}",
            date_peremption=datetime.now() + timedelta(days=random.randint(30, 365*3)),
            fournisseur_id=random.choice(fournisseurs).id
        )
        medicaments.append(medicament)
    
    db.session.add_all(medicaments)
    db.session.commit()
    print(f"{len(medicaments)} médicaments ont été générés avec succès!")

if __name__ == "__main__":
    # Assurez-vous que votre application Flask est initialisée correctement
    from pharmaweb import create_app
    app = create_app()
    with app.app_context():
        generate_medicaments()