import pandas as pd
from pharmaweb import mainapp
from pharmaweb.models import db, Medicament
import sys

app = mainapp()

def reset_database():
    """Supprime et recrée la base de données"""
    with app.app_context():
        try:
            db.session.query(Medicament).delete()
            db.session.commit()
            print("✅ Base de données vidée avec succès")
            return True
        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur lors de la suppression de la base : {str(e)}")
            return False

def safe_convert(value, convert_type, default):
    """Convertit une valeur de manière sécurisée"""
    try:
        if pd.isna(value) or value == '':
            return default
        return convert_type(value)
    except (ValueError, TypeError):
        return default

def import_from_excel(file_path):
    """Importe les médicaments depuis la feuille 'inventaire baraka'"""
    with app.app_context():
        try:
            # 1. Lecture du fichier avec gestion des valeurs vides
            df = pd.read_excel(
                file_path,
                sheet_name="inventaire baraka",
                engine='openpyxl',
                na_values=['', 'NA', 'N/A', 'NaN', 'nan', 'None', ' ']
            )
            print(f"✅ Fichier Excel chargé : {len(df)} lignes trouvées")

            # 2. Nettoyage des données
            # Compléter les DCI vides avec le nom commercial
            df['dci'] = df['dci'].fillna(df['nom_commercial'])
            
            # 3. Supprimer les lignes avec des champs obligatoires manquants
            df = df[~df['code_cip'].isna() & ~df['nom_commercial'].isna()]
            print(f"🔧 Lignes valides après nettoyage : {len(df)}")

            # 4. Importation avec conversion sécurisée
            medicaments = []
            for index, row in df.iterrows():
                try:
                    medicament = Medicament(
                        code_cip=str(row['code_cip']),
                        nom_commercial=str(row['nom_commercial']),
                        dci=str(row['dci']),
                        forme_galenique=str(row.get('forme_galenique', '')),
                        dosage=str(row.get('dosage', '')),
                        categorie=str(row.get('categorie', 'Non classé')),
                        stock_actuel=safe_convert(row.get('stock_actuel'), int, 0),
                        stock_minimum=safe_convert(row.get('stock_minimum'), int, 10),
                        prix_achat=safe_convert(row.get('prix_achat'), float, 0.0),
                        prix_vente=safe_convert(row.get('prix_vente'), float, 0.0),
                        tva=safe_convert(row.get('tva'), float, 0.0),
                        remboursable=safe_convert(row.get('remboursable'), bool, False),
                        conditionnement=str(row.get('conditionnement', '')),
                        date_peremption=row['date_peremption'] if not pd.isna(row.get('date_peremption')) else None
                    )
                    medicaments.append(medicament)
                except Exception as e:
                    print(f"⚠️ Erreur critique sur la ligne {index+2}: {str(e)}")
                    print(f"Contenu problématique: {row.to_dict()}")

            db.session.add_all(medicaments)
            db.session.commit()
            print(f"✅ {len(medicaments)} médicaments importés avec succès")
            return True

        except Exception as e:
            db.session.rollback()
            print(f"❌ Erreur critique lors de l'import : {str(e)}")
            return False

if __name__ == "__main__":
    file_path = "stock_medicaments.xlsx"
    print(f"⚡ Début du processus de réinitialisation et d'import")
    
    if not reset_database():
        print("❌ Échec de la réinitialisation")
        sys.exit(1)
    
    if import_from_excel(file_path):
        print("✔️ Processus terminé avec succès")
    else:
        print("❌ Échec de l'import")
        sys.exit(1)