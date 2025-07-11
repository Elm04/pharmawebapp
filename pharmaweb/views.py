from flask import Blueprint, render_template, redirect, url_for, flash, request, jsonify, current_app, session, make_response
from flask_login import login_required, current_user
from pharmaweb.extensions import db
from functools import wraps
from sqlalchemy.exc import IntegrityError
from datetime import timedelta
from sqlalchemy.orm import joinedload
from datetime import datetime
from flask import current_app
from werkzeug.utils import secure_filename
from flask_wtf.csrf import generate_csrf
from sqlalchemy import or_


from pharmaweb.models import (Utilisateur, Medicament, Patient, Fournisseur, 
                            ParametrePharmacie, Vente, LigneVente, Proforma)
from pharmaweb.forms import (UtilisateurForm, MedicamentForm, PatientForm, 
                            ParametresPharmacieForm, VenteForm, LigneVenteForm, ProformaForm)
from pharmaweb.decorators import admin_required, caissier_required
# from pharmaweb.utils.helpers import save_image
from datetime import datetime
import os



def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS
           
def register_filters(app):
    """Fonction à appeler depuis app.py"""
    from .filters import format_currency  # Import local
    app.jinja_env.filters['format_currency'] = format_currency

views = Blueprint('views', __name__)

# ---------------------------
# Routes communes
# ---------------------------


@views.route('/')
def index():
    if current_user.is_authenticated:
        if current_user.role == 'admin':
            return redirect(url_for('views.admin_dashboard'))
        elif current_user.role in ['caissier', 'pharmacien']:
            return redirect(url_for('views.ventes_dashboard'))
    return render_template('index.html')

@views.route('/test-ticket-ultime')
def test_ticket_ultime():
    from datetime import datetime
    
    # Cas de test extrêmes
    test_cases = [
        {"desc": "Panier normal", "panier": [{"id":1,"nom":"Test","prix":10,"quantite":2}]},
        {"desc": "Panier dict", "panier": {"1": {"id":1,"nom":"Test","prix":10,"quantite":2}}},
        {"desc": "Panier vide", "panier": []},
        {"desc": "Panier None", "panier": None},
        {"desc": "Panier méthode", "panier": {"items": lambda: [{"id":1,"nom":"Test","prix":10,"quantite":2}]}},
        {"desc": "Vente None", "vente": None, "panier": [{"id":1,"nom":"Test","prix":10,"quantite":2}]}
    ]
    
    results = []
    for case in test_cases:
        try:
            ticket = _generer_ticket(
                case.get("vente", Vente(numero_ticket="TEST", date_vente=datetime.now())),
                case["panier"]
            )
            results.append(f"{case['desc']}: SUCCÈS ({len(ticket['items'])} items)")
        except Exception as e:
            results.append(f"{case['desc']}: ÉCHEC - {str(e)}")
    
    return "<br>".join(results)


@views.route('/profile')
@login_required
def profile():
    return render_template('profile.html', user=current_user)

# ---------------------------
# Section Admin
# ---------------------------

@views.route('/admin/dashboard')
@login_required
@admin_required
def admin_dashboard():
    from datetime import date, timedelta
    from sqlalchemy import func
    
    # Statistiques de base
    stats = {
        'users': Utilisateur.query.count(),
        'medicaments': Medicament.query.count(),
        'patients': Patient.query.count(),
        'ventes_jour': Vente.query.filter(
            func.date(Vente.date_vente) == date.today()
        ).count(),
        'alertes': 0,  # À implémenter
        'stocks_bas': Medicament.query.filter(
            Medicament.stock_actuel < Medicament.stock_minimum
        ).count()
    }

    # Données pour les graphiques (avec valeurs par défaut)
    try:
        dates_7jours = [(date.today() - timedelta(days=i)).strftime('%d/%m')
                      for i in range(6, -1, -1)]
        
        montants_7jours = [
            db.session.query(func.sum(Vente.montant_total)).filter(
                func.date(Vente.date_vente) == (date.today() - timedelta(days=i))
            ).scalar() or 0
            for i in range(6, -1, -1)
        ]
        
        # Top médicaments
        top_medicaments = db.session.query(
            Medicament.nom_commercial,
            func.sum(LigneVente.quantite).label('total')
        ).join(LigneVente).group_by(Medicament.id).order_by(
            func.sum(LigneVente.quantite).desc()
        ).limit(5).all()
        
        top_medicaments_noms = [m[0] for m in top_medicaments]
        top_medicaments_qtes = [float(m[1]) for m in top_medicaments]
        
    except Exception as e:
        print(f"Erreur préparation données dashboard: {str(e)}")
        dates_7jours = []
        montants_7jours = []
        top_medicaments_noms = []
        top_medicaments_qtes = []
    
    # Dernières ventes
    dernieres_ventes = Vente.query.order_by(
        Vente.date_vente.desc()
    ).limit(5).all()

    return render_template(
        'admin/dashboard.html',
        stats=stats,
        dates_7jours=dates_7jours or [],  # Garantit une liste vide si None
        montants_7jours=montants_7jours or [],
        top_medicaments_noms=top_medicaments_noms or [],
        top_medicaments_qtes=top_medicaments_qtes or [],
        dernieres_ventes=dernieres_ventes
    )

@views.route('/admin/utilisateurs')
@login_required
@admin_required
def gestion_utilisateurs():
    users = Utilisateur.query.all()
    return render_template('admin/utilisateurs/liste.html', users=users)

from flask import render_template, redirect, url_for, flash, request
from werkzeug.security import generate_password_hash
from .forms import UtilisateurForm

@views.route('/admin/utilisateur/ajouter', methods=['GET', 'POST'])
@login_required
@admin_required
def ajouter_utilisateur():
    form = UtilisateurForm()
    
    if form.validate_on_submit():
        try:
            hashed_password = generate_password_hash(form.password.data)
            
            user = Utilisateur(
                nom=form.nom.data,
                prenom=form.prenom.data,
                email=form.email.data,
                telephone=form.telephone.data,
                role=form.role.data,
                login=form.login.data,
                password=hashed_password,
                actif=form.actif.data
            )
            
            db.session.add(user)
            db.session.commit()
            
            flash('Utilisateur créé avec succès!', 'success')
            return redirect(url_for('views.gestion_utilisateurs'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création de l'utilisateur: {str(e)}", 'danger')
    
    return render_template('admin/utilisateurs/ajouter.html', form=form)

@views.route('/admin/utilisateur/modifier/<int:id>', methods=['GET', 'POST'])
@login_required
@admin_required
def modifier_utilisateur(id):
    user = Utilisateur.query.get_or_404(id)
    form = UtilisateurForm(obj=user)
    
    if form.validate_on_submit():
        try:
            user.nom = form.nom.data
            user.prenom = form.prenom.data
            user.email = form.email.data
            user.telephone = form.telephone.data
            user.role = form.role.data
            user.login = form.login.data
            user.actif = form.actif.data
            
            if form.password.data:
                user.password = generate_password_hash(form.password.data)
            
            db.session.commit()
            flash('Utilisateur mis à jour avec succès!', 'success')
            return redirect(url_for('views.gestion_utilisateurs'))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la mise à jour: {str(e)}", 'danger')
    
    return render_template('admin/utilisateurs/modifier.html', form=form, user=user)

@views.route('/admin/utilisateur/activer/<int:id>')
@login_required
@admin_required
def activer_utilisateur(id):
    user = Utilisateur.query.get_or_404(id)
    
    try:
        user.actif = True
        db.session.commit()
        flash('Utilisateur activé avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de l'activation: {str(e)}", 'danger')
    
    return redirect(url_for('views.gestion_utilisateurs'))

@views.route('/admin/utilisateur/desactiver/<int:id>')
@login_required
@admin_required
def desactiver_utilisateur(id):
    user = Utilisateur.query.get_or_404(id)
    
    try:
        user.actif = False
        db.session.commit()
        flash('Utilisateur désactivé avec succès', 'warning')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la désactivation: {str(e)}", 'danger')
    
    return redirect(url_for('views.gestion_utilisateurs'))

@views.route('/admin/utilisateur/supprimer/<int:id>')
@login_required
@admin_required
def supprimer_utilisateur(id):
    user = Utilisateur.query.get_or_404(id)
    
    try:
        db.session.delete(user)
        db.session.commit()
        flash('Utilisateur supprimé avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression: {str(e)}", 'danger')
    
    return redirect(url_for('views.gestion_utilisateurs'))


# MEDICAMENTS 


# Configuration pour les uploads
UPLOAD_FOLDER = 'static/uploads/medicaments'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif'}

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@views.route('/admin/medicaments')
@login_required
def gestion_medicaments():
    page = request.args.get('page', 1, type=int)
    per_page = 10  # Nombre d'éléments par page
    search_term = request.args.get('search', '').strip()

    query = Medicament.query.order_by(Medicament.nom_commercial)
    
    if search_term:
        query = query.filter(
            or_(
                Medicament.code_cip.ilike(f'%{search_term}%'),
                Medicament.nom_commercial.ilike(f'%{search_term}%'),
                Medicament.dci.ilike(f'%{search_term}%')
            )
        )

    medicaments = query.paginate(page=page, per_page=per_page, error_out=False)
    
    return render_template('admin/medicaments/liste.html', 
                         medicaments=medicaments,
                         search_term=search_term)

def get_fournisseurs_choices():
    """Retourne les options pour le selecteur de fournisseurs"""
    choices = [(str(f.id), f.nom) for f in Fournisseur.query.order_by('nom')]
    choices.insert(0, ('None', '-- Aucun fournisseur --'))
    return choices

@views.route('/admin/medicament/ajouter', methods=['GET', 'POST'])
@login_required
def ajouter_medicament():
    form = MedicamentForm()
    form.fournisseur_id.choices = get_fournisseurs_choices()  # Initialisation des fournisseurs
    
    if form.validate_on_submit():
        try:
            # Gestion sécurisée du fournisseur_id
            fournisseur_id = None
            if form.fournisseur_id.data and form.fournisseur_id.data != 'None':
                try:
                    fournisseur_id = int(form.fournisseur_id.data)
                except (ValueError, TypeError):
                    flash('ID fournisseur invalide', 'danger')
                    return render_template('admin/medicaments/ajouter.html', form=form)

            # Création d'un nouveau médicament
            medicament = Medicament(
                code_cip=form.code_cip.data.strip(),  # Nettoyage des espaces
                nom_commercial=form.nom_commercial.data.strip(),
                dci=form.dci.data.strip(),
                forme_galenique=form.forme_galenique.data.strip() if form.forme_galenique.data else None,
                dosage=form.dosage.data.strip() if form.dosage.data else None,
                categorie=form.categorie.data,
                stock_actuel=int(form.stock_actuel.data),
                stock_minimum=int(form.stock_minimum.data),
                prix_achat=float(form.prix_achat.data) if form.prix_achat.data else None,
                prix_vente=float(form.prix_vente.data) if form.prix_vente.data else None,
                tva=float(form.tva.data) if form.tva.data else 0.0,
                remboursable=bool(form.remboursable.data),
                conditionnement=form.conditionnement.data.strip() if form.conditionnement.data else None,
                date_peremption=form.date_peremption.data,
                fournisseur_id=fournisseur_id  # Utilisation de la valeur déjà convertie
            )

            # Vérification de l'unicité du code CIP
            if Medicament.query.filter(Medicament.code_cip.ilike(form.code_cip.data.strip())).first():
                flash('Ce code CIP existe déjà', 'danger')
                return render_template('admin/medicaments/ajouter.html', form=form)
            
            db.session.add(medicament)
            db.session.commit()
            
            flash('Médicament ajouté avec succès!', 'success')
            return redirect(url_for('views.gestion_medicaments'))
            
        except ValueError as e:
            db.session.rollback()
            flash(f'Erreur de conversion numérique: {str(e)}', 'danger')
        except IntegrityError as e:
            db.session.rollback()
            flash(f'Erreur d\'intégrité base de données: {str(e)}', 'danger')
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur technique: {str(e)}', 'danger')
            current_app.logger.error(f"Erreur ajout médicament: {str(e)}", exc_info=True)
    
    return render_template('admin/medicaments/ajouter.html', form=form, mode_edition=False)

@views.route('/admin/medicament')
@views.route('/admin/medicament/edit/<int:medicament_id>', methods=['GET', 'POST'])
@login_required
def modifier_medicament(medicament_id):
    medicament = Medicament.query.get_or_404(medicament_id)
    form = MedicamentForm(obj=medicament)
    form.fournisseur_id.choices = get_fournisseurs_choices()

    if form.validate_on_submit():
        try:
            # Gestion spéciale du fournisseur
            if form.fournisseur_id.data == 'None':
                medicament.fournisseur_id = None
            else:
                medicament.fournisseur_id = form.fournisseur_id.data

            # Copie des autres champs
            for field in form:
                if field.name not in ['fournisseur_id', 'csrf_token']:
                    setattr(medicament, field.name, field.data)

            db.session.commit()
            flash('Modification réussie!', 'success')
            return redirect(url_for('views.gestion_medicaments'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur technique: {str(e)}', 'danger')

    return render_template('admin/medicaments/ajouter.html', 
                         form=form, 
                         medicament=medicament,
                         mode_edition=True)

@views.route('/admin/medicament/supprimer/<int:id>')
@login_required
def supprimer_medicament(id):
    medicament = Medicament.query.get_or_404(id)
    
    try:      
        db.session.delete(medicament)
        db.session.commit()
        flash('Médicament supprimé avec succès', 'success')
    except Exception as e:
        db.session.rollback()
        flash(f"Erreur lors de la suppression: {str(e)}", 'danger')
    
    return redirect(url_for('views.gestion_medicaments'))

# ---------------------------
# Section Ventes
# ---------------------------

@views.route('/ventes/<int:vente_id>/detail')
@login_required
@caissier_required
def detail_facture(vente_id):
    # Récupération de la vente
    vente = Vente.query.get_or_404(vente_id)
    
    # Vérification de la date (optionnel)
    if vente.date_vente.date() != datetime.today().date():
        flash("Accès restreint aux ventes du jour", 'warning')
        return redirect(url_for('views.ventes_dashboard'))

    # Récupération des lignes de vente
    lignes = db.session.query(
        LigneVente,
        Medicament.nom_commercial,
        Medicament.code_cip
    ).join(
        Medicament, LigneVente.medicament_id == Medicament.id
    ).filter(
        LigneVente.vente_id == vente_id
    ).all()

    # Récupération des paramètres de la pharmacie
    pharmacie = ParametrePharmacie.query.first()
    
    # Construction de l'adresse complète
    adresse_complete = f"{pharmacie.adresse_rue}, {pharmacie.adresse_ville}"
    if pharmacie.adresse_code_postal:
        adresse_complete += f", {pharmacie.adresse_code_postal}"
    if pharmacie.adresse_pays:
        adresse_complete += f", {pharmacie.adresse_pays}"

    # Construction des items de la vente
    items_list = []
    for ligne, nom, code_cip in lignes:
        items_list.append({
            'nom': nom,
            'cip': code_cip,
            'prix': float(ligne.prix_unitaire),
            'quantite': ligne.quantite,
            'total': float(ligne.prix_unitaire * ligne.quantite)
        })

    # Construction du ticket
    ticket = {
        'numero': vente.numero_ticket,
        'date': vente.date_vente.strftime('%d/%m/%Y %H:%M'),
        'ligne_vente': items_list,
        'total': float(vente.montant_total),
        'montant_regle': float(vente.montant_regle),
        'monnaie': float(vente.montant_regle - vente.montant_total),
        'caissier': f"{vente.caissier.prenom} {vente.caissier.nom}",
        'patient': f"{vente.client.nom} {vente.client.prenom}" if vente.client else "Non renseigné",
        'pharmacie': {
            'nom': pharmacie.nom_pharmacie,
            'adresse': adresse_complete,
            'telephone': pharmacie.telephone_principal,
            'telephone2': pharmacie.telephone_secondaire,
            'email': pharmacie.email,
            'site_web': pharmacie.site_web,
            'rccm': pharmacie.rccm,
            'tva': pharmacie.numero_tva,
            'ordre_pharmaciens': pharmacie.numero_ordre_pharmaciens,
            'responsable': pharmacie.responsable_legal,
            'logo': url_for('static', filename=pharmacie.chemin_logo.split('/')[-1]) if pharmacie.inclure_logo and pharmacie.chemin_logo else None
        }
    }

    return render_template('ventes/detail_vente.html', ticket=ticket, _items=items_list)

def _rechercher_medicaments(search_term=''):
    """Méthode utilitaire pour rechercher des médicaments en stock"""
    query = Medicament.query.filter(Medicament.stock_actuel > 0)
    
    if search_term:
        query = query.filter(
            (Medicament.nom_commercial.ilike(f'%{search_term}%')) |
            (Medicament.code_cip.ilike(f'%{search_term}%'))
        )
    
    return query.order_by(Medicament.nom_commercial).all()

def _ajouter_au_panier(medicament_id, quantite):
    """Méthode utilitaire pour ajouter un médicament au panier"""
    medicament = Medicament.query.get(medicament_id)
    if not medicament or quantite <= 0 or quantite > medicament.stock_actuel:
        return False
    
    item = {
        'id': medicament.id,
        'nom': medicament.nom_commercial,
        'prix': float(medicament.prix_vente),
        'quantite': quantite
    }
    
    if 'panier' not in session:
        session['panier'] = []
        session['total'] = 0.0
    
    session['panier'].append(item)
    session['total'] += item['prix'] * item['quantite']
    session.modified = True
    
    return True

def _creer_vente(panier, patient_id=None, mode_paiement='espèces', montant_regle=None):
    """Méthode utilitaire pour créer une vente en base"""
    if not panier:
        return None, "Panier vide"
    
    # Ajoutez cette validation
    for item in panier:
        medicament = Medicament.query.get(item['id'])
        if not medicament or medicament.stock_actuel < item['quantite']:
            return None, f"Stock insuffisant pour {item.get('nom', 'produit')}"
    
    total = sum(item['prix'] * item['quantite'] for item in panier)
    if montant_regle is None:
        montant_regle = total
    
    try:
        nouvelle_vente = Vente(
            numero_ticket=f"TKT-{datetime.now().strftime('%Y%m%d%H%M%S')}",
            utilisateur_id=current_user.id,
            patient_id=patient_id if patient_id != 0 else None,
            montant_total=float(total),
            montant_regle=float(montant_regle),
            mode_paiement=mode_paiement,
            date_vente=datetime.now()
        )
        
        db.session.add(nouvelle_vente)
        db.session.flush()
        
        for item in panier:
            medicament = Medicament.query.get(item['id'])
            ligne_vente = LigneVente(
                vente_id=nouvelle_vente.id,
                medicament_id=medicament.id,
                quantite=item['quantite'],
                prix_unitaire=item['prix'],
                tva=0.0,  # Valeur par défaut explicite
                remise=0.0  # Valeur par défaut explicite
            )
            medicament.stock_actuel -= item['quantite']
            db.session.add(ligne_vente)
        
        db.session.commit()
        return nouvelle_vente, None
        
    except Exception as e:
        db.session.rollback()
        return None, str(e)

def _generer_ticket(vente, panier):
    """Version finale totalement immunisée contre les erreurs"""
    # 1. Conversion ABSOLUMENT sécurisée des items
    items = []
    try:
        # Cas spécial pour les objets avec méthode .items()
        if hasattr(panier, 'items') and callable(panier.items):
            try:
                panier = list(panier.items())
            except:
                panier = []

        # Conversion en liste de dictionnaires standard
        if isinstance(panier, (list, tuple, set)):
            items = [
                {
                    'id': int(item.get('id', 0)),
                    'nom': str(item.get('nom', 'Produit inconnu')),
                    'prix': float(item.get('prix', 0)),
                    'quantite': int(item.get('quantite', 1))
                }
                for item in panier 
                if isinstance(item, (dict,))
            ]
        elif isinstance(panier, dict):
            items = [
                {
                    'id': int(v.get('id', k)),
                    'nom': str(v.get('nom', f'Produit {k}')),
                    'prix': float(v.get('prix', 0)),
                    'quantite': int(v.get('quantite', 1))
                }
                for k, v in panier.items()
                if isinstance(v, (dict,))
            ]
    except Exception as e:
        current_app.logger.error(f"ERREUR GRAVE - Conversion panier impossible: {str(e)}")
        items = []

    # 2. Calcul des totaux de secours
    total_items = sum(item['prix'] * item['quantite'] for item in items)
    
    # 3. Construction du ticket avec protections absolues
    ticket = {
        'numero': str(getattr(vente, 'numero_ticket', f'TKT-ERR-{datetime.now().timestamp()}')),
        'date': getattr(vente, 'date_vente', datetime.now()).strftime('%d/%m/%Y %H:%M'),
        'items': items,
        'total': float(getattr(vente, 'montant_total', total_items)),
        'montant_regle': float(getattr(vente, 'montant_regle', 0)),
        'monnaie': float(getattr(vente, 'montant_regle', 0) - getattr(vente, 'montant_total', total_items)),
        'caissier': (
            f"{current_user.prenom} {current_user.nom}" 
            if current_user and hasattr(current_user, 'prenom') and hasattr(current_user, 'nom') 
            else "Système"
        )
    }

    # Vérification finale
    assert isinstance(ticket['items'], list), "Items doit être une liste"
    current_app.logger.info(f"Ticket généré avec {len(ticket['items'])} articles")
    
    return ticket
    
@views.route('/ventes/dashboard')
@login_required
@caissier_required
def ventes_dashboard():
    # Gestion de la recherche
    search_term = request.args.get('recherche', '')
    medicaments = _rechercher_medicaments(search_term)
    
    
    # Statistiques (ancienne version)
    dernieres_ventes = Vente.query.filter(
        db.func.date(Vente.date_vente) == datetime.today().date()
    ).order_by(Vente.date_vente.desc()).limit(10).all()
    
    try:
        top_produit = db.session.query(
            Medicament.nom_commercial,
            db.func.sum(LigneVente.quantite).label('total')
        ).join(LigneVente, Medicament.id == LigneVente.medicament_id
        ).join(Vente, LigneVente.vente_id == Vente.id
        ).filter(
            db.func.date(Vente.date_vente) == datetime.today().date()
        ).group_by(Medicament.id
        ).order_by(db.func.sum(LigneVente.quantite).desc()
        ).first()
    except Exception as e:
        current_app.logger.error(f"Erreur requête top produit: {str(e)}")
        top_produit = None
    
    stats = {
        'ventes_jour': len(dernieres_ventes),
        'chiffre_jour': sum(v.montant_total for v in dernieres_ventes),
        'top_produit': top_produit
    }
    
    return render_template('ventes/dashboard.html',
                         medicaments=medicaments,
                         dernieres_ventes=dernieres_ventes,
                         stats=stats,
                         search_term=search_term)

def _valider_panier(panier):
    for item in panier:
        medicament = Medicament.query.get(item['id'])
        if not medicament or medicament.stock_actuel < item['quantite']:
            return False
    return True
    
@views.route('/retirer-du-panier/<int:index>')
@login_required
@caissier_required
def retirer_du_panier(index):
    if 'panier' in session and 0 <= index < len(session['panier']):
        # Mettre à jour le total
        session['total'] -= session['panier'][index]['prix'] * session['panier'][index]['quantite']
        
        # Retirer l'élément
        session['panier'].pop(index)
        
        # Si le panier est vide, le supprimer
        if not session['panier']:
            session.pop('panier')
            session.pop('total')
        else:
            session.modified = True
    
    return redirect(url_for('views.nouvelle_vente'))

# -----------------------
# GESTION DU PROFORMA
# -----------------------

@views.route('/proformas/nouveau', methods=['GET', 'POST'])
@login_required
@caissier_required
def nouvelle_proforma():
    form = ProformaForm()
    search_term = request.args.get('search', '').strip()
    
    # Récupération des médicaments filtrés
    query = Medicament.query.filter(Medicament.stock_actuel > 0)
    if search_term:
        query = query.filter(
            (Medicament.nom_commercial.ilike(f'%{search_term}%')) |
            (Medicament.code_cip.ilike(f'%{search_term}%'))
        )
    
    page = request.args.get('page', 1, type=int)
    medicaments = query.paginate(page=page, per_page=10)
    
    # Génération automatique de référence
    if not form.reference.data:
        last_proforma = Proforma.query.order_by(Proforma.id.desc()).first()
        last_id = last_proforma.id if last_proforma else 0
        form.reference.data = f"PRO-{datetime.now().strftime('%y%m%d')}-{last_id + 1:03d}"
    
    if form.validate_on_submit():
        if 'panier_proforma' not in session or not session['panier_proforma']:
            flash("Le panier est vide, ajoutez des produits", 'danger')
            return redirect(url_for('views.nouvelle_proforma'))
        
        try:
            # Calcul du montant total
            montant_total = sum(item['prix'] * item['quantite'] for item in session['panier_proforma'])
            
            nouvelle_proforma = Proforma(
                reference=form.reference.data,
                client_id=form.client.data.id,
                montant_total=montant_total,
                date_creation=datetime.now(),
                date_validite=form.date_validite.data,
                createur_id=current_user.id
            )
            
            db.session.add(nouvelle_proforma)
            
            # Ajout des détails
            for item in session['panier_proforma']:
                detail = Proforma(  # Supposant que vous avez un modèle Proforma
                    proforma_id=nouvelle_proforma.id,
                    medicament_id=item['medicament_id'],
                    quantite=item['quantite'],
                    prix_unitaire=item['prix']
                )
                db.session.add(detail)
            
            db.session.commit()
            session.pop('panier_proforma', None)
            
            flash('Proforma créée avec succès!', 'success')
            return redirect(url_for('views.liste_proformas', id=nouvelle_proforma.id))
            
        except Exception as e:
            db.session.rollback()
            flash(f"Erreur lors de la création: {str(e)}", 'danger')
            current_app.logger.error(f"Erreur création proforma: {str(e)}")
            total = sum(item['prix'] * item['quantite'] for item in session.get('panier_proforma', []))

    
    return render_template('proformas/nouveau.html', 
                         form=form, 
                         medicaments=medicaments,
                         search_term=search_term)
    
@views.route('/proformas/liste')
@login_required
def liste_proformas():
    page = request.args.get('page', 1, type=int)
    search = request.args.get('search', '').strip()
    
    query = Proforma.query.options(
        joinedload(Proforma.client),
        joinedload(Proforma.createur)
    )
    
    if search:
        query = query.filter(
            (Proforma.reference.ilike(f'%{search}%')) |
            (Patient.nom_complet.ilike(f'%{search}%'))
        )
    
    proformas = query.order_by(Proforma.date_creation.desc()).paginate(page=page, per_page=10)
    
    return render_template('proformas/liste.html', proformas=proformas, search_term=search)

@views.route('/proforma/<int:id>')
@login_required
def visualiser_proforma(id):
    proforma = Proforma.query.options(
        joinedload(Proforma.client),
        joinedload(Proforma.lignes).joinedload(Proforma.medicament)
    ).get_or_404(id)
    
    return render_template('proformas/detail.html', 
                         proforma=proforma,
                         search_term=request.args.get('search', ''))
    


@views.route('/proformas/ajouter', methods=['POST'])
@login_required
@caissier_required
def ajouter_produit_proforma():
    if not request.form:
        flash("Format de requête invalide", 'danger')
        return redirect(url_for('views.nouvelle_proforma'))

    try:
        medicament_id = request.form.get('medicament_id')
        quantite = request.form.get('quantite', '1')
        
        if not medicament_id:
            raise ValueError("ID médicament manquant")
        
        if not quantite.isdigit():
            raise ValueError("La quantité doit être un nombre entier")
            
        quantite = int(quantite)
        if quantite <= 0:
            raise ValueError("La quantité doit être positive")

        medicament = Medicament.query.get_or_404(medicament_id)
        
        if medicament.stock_actuel < quantite:
            raise ValueError(f"Stock insuffisant. Disponible: {medicament.stock_actuel}")

        # Initialisation ou mise à jour du panier
        panier = session.get('panier_proforma', [])
        existing_item = next((item for item in panier if item['medicament_id'] == medicament.id), None)
        
        if existing_item:
            existing_item['quantite'] += quantite
        else:
            panier.append({
                'medicament_id': medicament.id,
                'nom': medicament.nom_commercial,
                'prix': float(medicament.prix_vente),
                'quantite': quantite
            })
        
        session['panier_proforma'] = panier
        
        flash(f"{quantite} {medicament.nom_commercial} ajouté(s) au panier", 'success')
        
    except ValueError as e:
        flash(f"Erreur: {str(e)}", 'danger')
    except Exception as e:
        flash("Une erreur est survenue", 'danger')
        current_app.logger.error(f"Erreur ajout proforma: {str(e)}")
    
    return redirect(url_for('views.nouvelle_proforma',
                          search=request.args.get('search', '')))

@views.route('/proformas/supprimer/<int:medicament_id>', methods=['POST'])
@login_required
@caissier_required
def supprimer_produit_proforma(medicament_id):
    try:
        panier = session.get('panier_proforma', [])
        panier = [item for item in panier if item['medicament_id'] != medicament_id]
        session['panier_proforma'] = panier
        flash("Produit retiré du panier", 'success')
    except Exception as e:
        flash("Erreur lors de la suppression", 'danger')
        current_app.logger.error(f"Erreur suppression produit proforma: {str(e)}")
    
    return redirect(url_for('views.nouvelle_proforma'))

@views.route('/api/panier-proforma', methods=['GET'])
def get_panier_proforma():
    return jsonify({
        'items': session.get('panier_proforma', []),
        'total': sum(item['prix'] * item['quantite'] for item in session.get('panier_proforma', []))
    })
    
@views.route('/panier-proforma', methods=['POST'])
def afficher_panier_proforma():
    # Récupération des paramètres de la pharmacie
    pharmacie_db = ParametrePharmacie.query.first()
    
    # Construction de l'adresse complète
    adresse_complete = f"{pharmacie_db.adresse_rue}, {pharmacie_db.adresse_ville}"
    if pharmacie_db.adresse_code_postal:
        adresse_complete += f", {pharmacie_db.adresse_code_postal}"
    if pharmacie_db.adresse_pays:
        adresse_complete += f", {pharmacie_db.adresse_pays}"

    # Préparation des données de la pharmacie
    pharmacie = {
        'nom': pharmacie_db.nom_pharmacie,
        'adresse': adresse_complete,
        'telephone': pharmacie_db.telephone_principal,
        'telephone2': pharmacie_db.telephone_secondaire,
        'email': pharmacie_db.email,
        'site_web': pharmacie_db.site_web,
        'rccm': pharmacie_db.rccm,
        'tva': pharmacie_db.numero_tva,
        'ordre_pharmaciens': pharmacie_db.numero_ordre_pharmaciens,
        'responsable': pharmacie_db.responsable_legal,
        'logo': url_for('static', filename=pharmacie_db.chemin_logo.split('/')[-1]) if pharmacie_db.inclure_logo and pharmacie_db.chemin_logo else None
    }
    
    # Récupération du panier proforma
    panier = session.get('panier_proforma', [])
    total = sum(item['prix'] * item['quantite'] for item in panier)
    
    return render_template('proformas/panier_complet.html',
                        pharmacie=pharmacie,
                        items=panier,
                        total=total,
                        now=datetime.now())

@views.route('/api/vider-panier-proforma', methods=['POST'])
@login_required
def api_panier_proforma():
    session.pop('panier_proforma', None)
    return jsonify({'success': True, 'message': 'Panier vidé'})

@views.route('/vider-panier-proforma', methods=['POST'])
@login_required
def vider_panier_proforma():
    session.pop('panier_proforma', None)
    return redirect(url_for('views.nouvelle_proforma'))




@views.route('/ventes/nouvelle-vente', methods=['GET', 'POST'])
@login_required
@caissier_required
def nouvelle_vente():
    # Initialisation
    form = VenteForm()
    form.patient_id.choices = [(0, "Aucun")] + [(p.id, f"{p.nom} {p.prenom}") for p in Patient.query.all()]
    search_term = request.args.get('recherche', '')
    
    # Gestion du panier (initialisation)
    if 'panier' not in session:
        session['panier'] = []  # Garantit que c'est toujours une liste
        session['total'] = 0.0

    # 1. Gestion de la recherche
    medicaments = _rechercher_medicaments(search_term)

    # 2. Ajout au panier
    if request.method == 'POST' and 'medicament_id' in request.form:
        medicament_id = int(request.form['medicament_id'])
        quantite = int(request.form['quantite'])
        
        if not _ajouter_au_panier(medicament_id, quantite):
            flash("Erreur lors de l'ajout au panier", 'danger')
            
        return redirect(url_for('views.nouvelle_vente', recherche=search_term))

    # 3. Finalisation de la vente
    if form.validate_on_submit():
        csrf_token = generate_csrf()
        # Validation initiale
        if not session['panier']:
            flash("Le panier est vide", 'warning')
            return redirect(url_for('views.nouvelle_vente'))

        # Conversion explicite du panier (sécurité renforcée)
        panier = []
        try:
            if isinstance(session['panier'], dict):
                panier = list(session['panier'].values())
            elif isinstance(session['panier'], list):
                panier = session['panier']
            else:
                raise ValueError("Format de panier invalide")
                
            # Validation du stock
            for item in panier:
                if not isinstance(item, dict) or 'id' not in item:
                    raise ValueError("Structure d'item invalide")
                
                medicament = Medicament.query.get(item['id'])
                if not medicament or medicament.stock_actuel < item.get('quantite', 0):
                    raise ValueError(f"Stock insuffisant pour {item.get('nom', 'produit')}")
                    
        except Exception as e:
            flash(f"Erreur de validation : {str(e)}", 'danger')
            return redirect(url_for('views.nouvelle_vente'))

        # Validation financière
        if form.montant_regle.data < session['total']:
            flash("Montant insuffisant", 'danger')
            return redirect(url_for('views.nouvelle_vente'))

        # Création de la vente (version robuste)
        try:
            vente, error = _creer_vente(
                panier=panier,  # Utilise la version convertie/validée
                patient_id=form.patient_id.data if form.patient_id.data != 0 else None,
                mode_paiement=form.mode_paiement.data,
                montant_regle=float(form.montant_regle.data)
            )
            
            if error or vente is None:
                flash(f"Erreur création vente: {error or 'objet vente non créé'}", 'danger')
                return redirect(url_for('views.nouvelle_vente'))
            
            
            if not isinstance(session['panier'], (list, dict)) or hasattr(session['panier'], 'items'):
                current_app.logger.error(f"Format de panier invalide: {type(session['panier'])}")
                session['panier'] = []  # Réinitialisation sécurisée
            
            # Génération du ticket
            ticket = _generer_ticket(vente, session['panier'])
    
            
            # Nettoyage de la session
            session.pop('panier', None)
            session.pop('total', None)
            
            # Journalisation réussite
            current_app.logger.info(f"Vente {vente.numero_ticket} créée avec succès")
            return render_template('ventes/ticket.html', ticket=ticket)
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erreur vente : {str(e)}")
            flash(f"Erreur système : {str(e)}", 'danger')
            return redirect(url_for('views.nouvelle_vente'))
    
    # Affichage normal (GET)
    return render_template(
        'ventes/nouvelle_vente.html',
        form=form,
        medicaments=medicaments,
        search_term=search_term,
        panier=session.get('panier', []),
        total=session.get('total', 0.0),
        )
    




# ---------------------------
# Gestion des ventes pour l'admin
# ---------------------------

@views.route('/admin/ventes')
@login_required
@admin_required
def gestion_ventes():
    # Par défaut, afficher les ventes du jour
    date_filtre = request.args.get('date', datetime.today().strftime('%Y-%m-%d'))
    utilisateur_id = request.args.get('utilisateur_id')
    
    try:
        date_filtre = datetime.strptime(date_filtre, '%Y-%m-%d').date()
    except ValueError:
        date_filtre = datetime.today().date()
    
    # Construction de la requête de base
    query = Vente.query.filter(
        db.func.date(Vente.date_vente) == date_filtre
    ).order_by(Vente.date_vente.desc())
    
    # Filtre par caissier si spécifié
    if utilisateur_id and utilisateur_id != 'tous':
        query = query.filter(Vente.utilisateur_id == utilisateur_id)
    
    ventes = query.all()
    
    # Calcul des statistiques
    stats = {
        'total_ventes': len(ventes),
        'chiffre_affaire': sum(v.montant_total for v in ventes),
        'moyenne_vente': sum(v.montant_total for v in ventes) / len(ventes) if ventes else 0
    }
    
    # Liste des caissiers pour le filtre
    caissiers = Utilisateur.query.filter(
        Utilisateur.role == 'caissier',
        Utilisateur.actif == True
    ).all()
    
    return render_template('admin/ventes/liste.html',
                         ventes=ventes,
                         stats=stats,
                         caissiers=caissiers,
                         date_selected=date_filtre.strftime('%Y-%m-%d'),
                         utilisateur_selected=utilisateur_id)

@views.route('/admin/vente/<int:vente_id>')
@login_required
@admin_required
def detail_vente(vente_id):
    vente = Vente.query.get_or_404(vente_id)
    return render_template('admin/ventes/details.html', vente=vente)

@views.route('/admin/ventes/rapport')
@login_required
@admin_required
def rapport_ventes():
    # Paramètres du rapport
    date_debut = request.args.get('date_debut', (datetime.today() - timedelta(days=7)).strftime('%Y-%m-%d'))
    date_fin = request.args.get('date_fin', datetime.today().strftime('%Y-%m-%d'))
    group_by = request.args.get('group_by', 'jour')  # jour, caissier, medicament
    
    try:
        date_debut = datetime.strptime(date_debut, '%Y-%m-%d').date()
        date_fin = datetime.strptime(date_fin, '%Y-%m-%d').date()
    except ValueError:
        date_debut = (datetime.today() - timedelta(days=7)).date()
        date_fin = datetime.today().date()
    
    # Requête de base
    if group_by == 'jour':
        # Groupement par jour
        data = db.session.query(
            db.func.date(Vente.date_vente).label('periode'),
            db.func.count(Vente.id).label('nb_ventes'),
            db.func.sum(Vente.montant_total).label('chiffre_affaire')
        ).filter(
            db.func.date(Vente.date_vente) >= date_debut,
            db.func.date(Vente.date_vente) <= date_fin
        ).group_by(
            db.func.date(Vente.date_vente)
        ).order_by(
            db.func.date(Vente.date_vente)
        ).all()
        
        labels = [d.periode.strftime('%d/%m/%Y') for d in data]
        valeurs = [float(d.chiffre_affaire) for d in data]
        
    elif group_by == 'caissier':
        # Groupement par caissier
        data = db.session.query(
            Utilisateur.prenom.label('periode'),
            db.func.count(Vente.id).label('nb_ventes'),
            db.func.sum(Vente.montant_total).label('chiffre_affaire')
        ).join(Vente).filter(
            db.func.date(Vente.date_vente) >= date_debut,
            db.func.date(Vente.date_vente) <= date_fin,
            Utilisateur.role == 'caissier'
        ).group_by(
            Utilisateur.id
        ).order_by(
            db.func.sum(Vente.montant_total).desc()
        ).all()
        
        labels = [d.periode for d in data]
        valeurs = [float(d.chiffre_affaire) for d in data]
        
    elif group_by == 'medicament':
        # Groupement par médicament
        data = db.session.query(
            Medicament.nom_commercial.label('periode'),
            db.func.sum(LigneVente.quantite).label('quantite'),
            db.func.sum(LigneVente.quantite * LigneVente.prix_unitaire).label('chiffre_affaire')
        ).join(LigneVente).join(Vente).filter(
            db.func.date(Vente.date_vente) >= date_debut,
            db.func.date(Vente.date_vente) <= date_fin
        ).group_by(
            Medicament.id
        ).order_by(
            db.func.sum(LigneVente.quantite * LigneVente.prix_unitaire).desc()
        ).limit(10).all()
        
        labels = [d.periode for d in data]
        valeurs = [float(d.chiffre_affaire) for d in data]
    
    return render_template('admin/ventes/rapport.html',
                         data=data,
                         labels=labels,
                         valeurs=valeurs,
                         date_debut=date_debut.strftime('%Y-%m-%d'),
                         date_fin=date_fin.strftime('%Y-%m-%d'),
                         group_by=group_by)
    

# ------------------------------------
# Paramètre pharmacie 
# ------------------------------------
@views.route('/admin/parametres', methods=['GET', 'POST'])
@login_required
@admin_required  # Assurez-vous que seul l'admin peut modifier
def parametres_pharmacie():
    parametres = ParametrePharmacie.query.first()
    
    # Si aucun paramètre n'existe, créez-en un avec les valeurs par défaut
    if not parametres:
        parametres = ParametrePharmacie()
        db.session.add(parametres)
        db.session.commit()
    
    form = ParametresPharmacieForm(obj=parametres)
    
    if form.validate_on_submit():
        try:
            form.populate_obj(parametres)
            
            # Gestion du fichier logo
            if 'logo' in request.files:
                file = request.files['logo']
                if file.filename != '':
                    # Créez le dossier s'il n'existe pas
                    upload_dir = os.path.join(current_app.root_path, 'static', 'uploads', 'logos')
                    os.makedirs(upload_dir, exist_ok=True)  # Crée le dossier si inexistant
                    
                    # Sécurisez et sauvegardez le fichier
                    filename = secure_filename(file.filename)
                    filepath = os.path.join(upload_dir, filename)
                    file.save(filepath)
                    parametres.chemin_logo = f'/static/uploads/logos/{filename}'
            
            db.session.commit()
            flash('Paramètres mis à jour avec succès!', 'success')
            return redirect(url_for('views.parametres_pharmacie'))
            
        except Exception as e:
            db.session.rollback()
            flash(f'Erreur lors de la mise à jour: {str(e)}', 'danger')
    
    return render_template('admin/parametres.html', 
                         form=form, 
                         parametres=parametres)
    
@views.route('/alertes')
@login_required
def alertes():
    # Produits avec stock bas (moins que le stock minimum défini)
    stock_bas = Medicament.query.filter(
        Medicament.stock_actuel < Medicament.stock_minimum
    ).all()
    
    # Produits proches de la péremption (dans les 30 prochains jours)
    seuil_peremption = datetime.now().date() + timedelta(days=30)
    produits_peremption = Medicament.query.filter(
        Medicament.date_peremption <= seuil_peremption,
        Medicament.date_peremption >= datetime.now().date()
    ).order_by(Medicament.date_peremption).all()
    
    return render_template('admin/alertes.html', 
                         stock_bas=stock_bas,
                         produits_peremption=produits_peremption)