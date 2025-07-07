import pandas as pd
import re
import random
from pharmaweb import create_app
from pharmaweb.models import db, Medicament

app = create_app()

# Définir CATEGORIES_MEDICAMENTS
CATEGORIES_MEDICAMENTS = [
    ('ANTIBIOTIQUES_PENICILLINES', 'Pénicillines'),
    ('ANTIBIOTIQUES_MACROLIDES', 'Macrolides'),
    ('ANALGESIQUES_OPIOIDES', 'Opioïdes'),
    ('CARDIO_ANTIHYPERTENSEURS', 'Antihypertenseurs')
]

# Dictionnaire de référence pour la génération des noms
MEDICAMENTS_REFERENCE = {
    'ANTIBIOTIQUES_PENICILLINES': {
        'prefixes': ['Amoxi', 'Augmentin', 'Clamoxyl', 'Oracilline', 'Penicline'],
        'suffixes': ['-250', '-500', '-1000', ' LP', ' Enfant', ' Adult']
    },
    'ANTIBIOTIQUES_MACROLIDES': {
        'prefixes': ['Azithro', 'Clari', 'Roxi', 'Josacine', 'Erythro'],
        'suffixes': ['-250', '-500', ' LP', ' Suspension', ' Pediatric']
    },
    'ANALGESIQUES_OPIOIDES': {
        'prefixes': ['Codoliprane', 'Tramadol', 'Morphine', 'Oxynorm', 'Paregoric'],
        'suffixes': ['-20', '-50', ' LP', ' Soluble', ' Forte']
    },
    'CARDIO_ANTIHYPERTENSEURS': {
        'prefixes': ['Amlor', 'Coveram', 'Lasilix', 'Zestril', 'Cardoril'],
        'suffixes': ['-5', '-10', ' Comp', ' LP', ' SR']
    }
}

def normaliser_cip(code_cip):
    """Normalise le code CIP en supprimant les espaces et caractères spéciaux"""
    if pd.isna(code_cip) or code_cip is None:
        return None
    code_str = str(code_cip)
    code_nettoye = re.sub(r'[^a-zA-Z0-9]', '', code_str)
    return code_nettoye.upper()

def get_categorie_key(display_name):
    """Trouve la clé de catégorie à partir du nom affiché"""
    if pd.isna(display_name) or display_name is None:
        return None
    for key, name in CATEGORIES_MEDICAMENTS:
        if name.lower() == str(display_name).lower():
            return key
    return None

def generer_nom_commercial(dci, categorie_display, forme, dosage):
    """Génère un nom commercial basé sur la catégorie"""
    if pd.isna(categorie_display):
        return f"{str(dci)[:10].capitalize()} {dosage} {str(forme)[:10]}"
    
    categorie_key = get_categorie_key(categorie_display)
    
    if not categorie_key or categorie_key not in MEDICAMENTS_REFERENCE:
        return f"{str(dci)[:10].capitalize()} {dosage} {str(forme)[:10]}"
    
    ref = MEDICAMENTS_REFERENCE[categorie_key]
    prefix = random.choice(ref['prefixes'])
    suffix = random.choice(ref['suffixes'])
    
    forme = str(forme).lower()
    if 'sirop' in forme:
        suffix = random.choice([' Sirop', ' Suspension'])
    elif 'comprime' in forme or 'comprimé' in forme:
        suffix = random.choice([' Comp', ' LP'])
    
    return f"{prefix}{suffix}"

def importer_medicaments(fichier_excel):
    try:
        # 1. Chargement du fichier
        df = pd.read_excel(fichier_excel, na_values=['', 'NA', 'N/A'])
        
        # Vérification des colonnes obligatoires
        colonnes_requises = ['code_cip', 'nom_commercial', 'dci','date_peremption']
        for col in colonnes_requises:
            if col not in df.columns:
                return False, f"Colonne obligatoire manquante: {col}. Veuillez ajouter cette colonne à votre fichier Excel."
        
        if 'categorie' not in df.columns:
            df['categorie'] = 'Autre'
        
        # 2. Nettoyage des données
        df = df.where(pd.notna(df), None)
        df['code_cip'] = df['code_cip'].apply(normaliser_cip)
        
        # 3. Génération des noms manquants si nécessaire
        if 'nom_commercial' in df.columns:
            mask = df['nom_commercial'].isna() | (df['nom_commercial'].str.strip() == '')
            df.loc[mask, 'nom_commercial'] = df[mask].apply(
                lambda x: generer_nom_commercial(
                    x['dci'],
                    x['categorie'],
                    x.get('forme_galenique', ''),
                    x.get('dosage', '')
                ), axis=1
            )
        
        # 4. Validation des catégories
        df['categorie_valide'] = df['categorie'].apply(
            lambda x: any(str(x).lower() == name.lower() for _, name in CATEGORIES_MEDICAMENTS)
        )
        
        # 5. Importation
        with app.app_context():
            for _, row in df.iterrows():
                if not row['categorie_valide']:
                    continue
                    
                medicament = Medicament(
                    code_cip=row['code_cip'],
                    nom_commercial=row['nom_commercial'],
                    dci=row['dci'],
                    categorie=row['categorie'],
                    forme_galenique=row.get('forme_galenique'),
                    dosage=row.get('dosage'),
                    stock_actuel=int(row.get('stock_actuel', 0)),
                    stock_minimum=int(row.get('stock_minimum', 10)),
                    prix_achat=float(row.get('prix_achat', 0)) if pd.notna(row.get('prix_achat')) else None,
                    prix_vente=float(row.get('prix_vente', 0)) if pd.notna(row.get('prix_vente')) else None,
                    tva=float(row.get('tva', 0)),
                    remboursable=bool(row.get('remboursable', False)),
                    conditionnement=row.get('conditionnement'),
                    date_peremption=row['date_peremption'],
                    fournisseur_id=row.get('fournisseur_id')
                )
                db.session.add(medicament)
            
            db.session.commit()
            return True, f"Import réussi : {len(df)} médicaments traités ({sum(df['categorie_valide'])} avec catégorie valide)"
            
    except Exception as e:
        return False, f"Erreur lors de l'import : {str(e)}"

if __name__ == '__main__':
    resultat, message = importer_medicaments('stock_medicaments.xlsx')
    print(message)