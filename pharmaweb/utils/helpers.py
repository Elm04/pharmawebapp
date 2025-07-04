import os
from datetime import datetime
from werkzeug.utils import secure_filename
from flask import current_app, flash
from PIL import Image
import io
import csv
from pharmaweb.models import Medicament, MouvementStock, Patient, Commande
from pharmaweb import db

# --------------------------
# Gestion des fichiers
# --------------------------

def allowed_file(filename, allowed_extensions):
    """Vérifie si l'extension du fichier est autorisée"""
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in allowed_extensions

def save_uploaded_file(file, subfolder='', allowed_extensions=None, resize=None):
    """
    Sauvegarde un fichier uploadé avec gestion sécurisée
    Args:
        file: Fichier à sauvegarder
        subfolder: Sous-dossier dans le dossier upload
        allowed_extensions: Liste des extensions autorisées
        resize: Tuple (width, height) pour redimensionner les images
    Returns:
        Chemin relatif du fichier sauvegardé ou None en cas d'échec
    """
    if not file or file.filename == '':
        return None

    if allowed_extensions and not allowed_file(file.filename, allowed_extensions):
        return None

    # Sécurisation du nom de fichier
    filename = secure_filename(file.filename)
    upload_dir = os.path.join(current_app.config['UPLOAD_FOLDER'], subfolder)

    # Création du dossier s'il n'existe pas
    os.makedirs(upload_dir, exist_ok=True)

    # Génération d'un nom unique pour éviter les collisions
    file_ext = filename.rsplit('.', 1)[1].lower()
    unique_filename = f"{datetime.now().strftime('%Y%m%d%H%M%S')}_{filename}"
    filepath = os.path.join(upload_dir, unique_filename)

    try:
        # Traitement spécial pour les images
        if resize and file_ext in ['jpg', 'jpeg', 'png', 'gif']:
            image = Image.open(file.stream)
            image.thumbnail(resize)
            image.save(filepath)
        else:
            file.save(filepath)
        
        # Retourne le chemin relatif pour le stockage en base
        return os.path.join(subfolder, unique_filename) if subfolder else unique_filename
    except Exception as e:
        current_app.logger.error(f"Erreur sauvegarde fichier: {str(e)}")
        return None

# --------------------------
# Gestion des médicaments
# --------------------------

def check_stock_alert(medicament_id):
    """Vérifie les alertes de stock pour un médicament"""
    medicament = Medicament.query.get(medicament_id)
    if not medicament:
        return False
    
    alerts = []
    if medicament.stock_actuel <= 0:
        alerts.append(('rupture_stock', 'Rupture de stock'))
    elif medicament.stock_actuel < medicament.stock_minimum:
        alerts.append(('seuil_minimum', f'Stock faible ({medicament.stock_actuel} unités)'))
    
    # Vérification de la date de péremption
    if medicament.date_peremption and medicament.date_peremption < datetime.now().date():
        alerts.append(('peremption', 'Médicament périmé'))
    
    return alerts

def update_stock(medicament_id, quantite, type_mouvement, user_id, reference_type=None, reference_id=None):
    """
    Met à jour le stock d'un médicament et enregistre le mouvement
    Args:
        medicament_id: ID du médicament
        quantite: Quantité à ajouter/soustraire (positive pour entrée, négative pour sortie)
        type_mouvement: 'entree', 'sortie', 'inventaire', 'ajustement'
        user_id: ID de l'utilisateur effectuant l'opération
        reference_type: Type de référence ('achat', 'vente', 'ordonnance')
        reference_id: ID de la référence
    Returns:
        Booléen indiquant le succès de l'opération
    """
    try:
        medicament = Medicament.query.get(medicament_id)
        if not medicament:
            return False

        # Mise à jour du stock
        if type_mouvement in ['entree', 'inventaire']:
            medicament.stock_actuel += quantite
        elif type_mouvement in ['sortie', 'ajustement']:
            medicament.stock_actuel -= quantite

        # Enregistrement du mouvement
        mouvement = MouvementStock(
            medicament_id=medicament_id,
            type_mouvement=type_mouvement,
            quantite=abs(quantite),
            utilisateur_id=user_id,
            reference_type=reference_type,
            reference_id=reference_id
        )

        db.session.add(mouvement)
        db.session.commit()
        return True
    except Exception as e:
        current_app.logger.error(f"Erreur mise à jour stock: {str(e)}")
        db.session.rollback()
        return False

# --------------------------
# Génération de codes
# --------------------------

def generate_patient_code(nom, prenom):
    """Génère un code patient unique"""
    base_code = f"{nom[:3].upper()}{prenom[:3].upper()}"
    existing = Patient.query.filter(Patient.code_patient.like(f"{base_code}%")).count()
    return f"{base_code}{existing + 1:03d}"

def generate_order_number():
    """Génère un numéro de commande unique"""
    today = datetime.now().strftime('%Y%m%d')
    last_order = Commande.query.order_by(Commande.id.desc()).first()
    seq = 1 if not last_order else int(last_order.reference.split('-')[-1]) + 1
    return f"CMD-{today}-{seq:04d}"

# --------------------------
# Export de données
# --------------------------

def export_to_csv(query, fields, filename):
    """
    Exporte une requête SQLAlchemy en CSV
    Args:
        query: Requête SQLAlchemy
        fields: Liste des champs à exporter
        filename: Nom du fichier de sortie
    Returns:
        Chemin du fichier généré
    """
    output = io.StringIO()
    writer = csv.writer(output)
    
    # En-têtes
    writer.writerow(fields)
    
    # Données
    for item in query:
        writer.writerow([getattr(item, field) for field in fields])
    
    # Sauvegarde dans le dossier d'export
    export_dir = os.path.join(current_app.config['UPLOAD_FOLDER'])