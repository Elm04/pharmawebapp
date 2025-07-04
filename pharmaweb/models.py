from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from pharmaweb.extensions import db


class Utilisateur(db.Model, UserMixin):
    __tablename__ = 'utilisateurs'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    telephone = db.Column(db.String(20))
    role = db.Column(db.Enum('admin', 'pharmacien', 'caissier', 'preparateur', name='roles'), nullable=False)
    login = db.Column(db.String(50), unique=True, nullable=False)
    password = db.Column(db.String(255), nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    actif = db.Column(db.Boolean, default=True)
    
    # Relations
    ordonnances = db.relationship('Ordonnance', backref='validateur', lazy=True)
    ventes = db.relationship('Vente', backref='caissier', lazy=True)
    mouvements_stock = db.relationship('MouvementStock', backref='operateur', lazy=True)
    alertes = db.relationship('Alerte', backref='responsable', lazy=True)
    
    def set_password(self, password):
        self.password = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password, password)
    

class Patient(db.Model):
    __tablename__ = 'patients'
    
    id = db.Column(db.Integer, primary_key=True)
    code_patient = db.Column(db.String(20), unique=True, nullable=False)
    nom = db.Column(db.String(50), nullable=False)
    prenom = db.Column(db.String(50), nullable=False)
    date_naissance = db.Column(db.Date)
    sexe = db.Column(db.Enum('M', 'F', 'Autre', name='sexes'))
    groupe_sanguin = db.Column(db.String(5))
    adresse = db.Column(db.Text)
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    assurance = db.Column(db.String(100))
    numero_assurance = db.Column(db.String(50))
    allergies = db.Column(db.Text)
    antecedents = db.Column(db.Text)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relations
    ordonnances = db.relationship('Ordonnance', backref='patient', lazy=True)
    ventes = db.relationship('Vente', backref='client', lazy=True)

class Fournisseur(db.Model):
    __tablename__ = 'fournisseurs'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    contact = db.Column(db.String(50))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(100))
    adresse = db.Column(db.Text)
    informations_bancaires = db.Column(db.Text)
    notes = db.Column(db.Text)
    actif = db.Column(db.Boolean, default=True)
    
    # Relations
    commandes = db.relationship('Commande', backref='fournisseur', lazy=True)
    medicaments = db.relationship('Medicament', backref='fournisseur_principal', lazy=True)

class CategorieMedicament(db.Model):
    __tablename__ = 'categories_medicaments'
    
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    
    # Relations
    medicaments = db.relationship('Medicament', backref='categorie', lazy=True)

class Medicament(db.Model):
    __tablename__ = 'medicaments'
    
    id = db.Column(db.Integer, primary_key=True)
    code_cip = db.Column(db.String(50), unique=True, nullable=False)
    nom_commercial = db.Column(db.String(100), nullable=False)
    dci = db.Column(db.String(100), nullable=False)
    forme_galenique = db.Column(db.String(50))
    dosage = db.Column(db.String(50))
    categorie_id = db.Column(db.Integer, db.ForeignKey('categories_medicaments.id'))
    stock_actuel = db.Column(db.Integer, default=0)
    stock_minimum = db.Column(db.Integer, default=10)
    prix_achat = db.Column(db.Numeric(10, 2))
    prix_vente = db.Column(db.Numeric(10, 2))
    tva = db.Column(db.Numeric(5, 2), default=0)
    remboursable = db.Column(db.Boolean, default=False)
    conditionnement = db.Column(db.String(50))
    date_peremption = db.Column(db.Date)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'))
    image_path = db.Column(db.String(255))
    
    # Relations
    lignes_ordonnance = db.relationship('LigneOrdonnance', backref='medicament', lazy=True)
    lignes_vente = db.relationship('LigneVente', backref='medicament', lazy=True)
    mouvements_stock = db.relationship('MouvementStock', backref='medicament', lazy=True)
    alertes = db.relationship('Alerte', backref='medicament', lazy=True)
    proforma_details = db.relationship('ProformaDetail', backref='medicament', lazy=True)

class Commande(db.Model):
    __tablename__ = 'commandes'
    
    id = db.Column(db.Integer, primary_key=True)
    fournisseur_id = db.Column(db.Integer, db.ForeignKey('fournisseurs.id'), nullable=False)
    date_commande = db.Column(db.DateTime, nullable=False)
    date_reception = db.Column(db.DateTime)
    statut = db.Column(db.String(50), nullable=False)
    montant_total = db.Column(db.Numeric(10, 2))
    notes = db.Column(db.Text)

class Ordonnance(db.Model):
    __tablename__ = 'ordonnances'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_ordonnance = db.Column(db.String(50), unique=True, nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medecin = db.Column(db.String(100))
    date_prescription = db.Column(db.Date)
    date_validation = db.Column(db.DateTime)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'))
    notes = db.Column(db.Text)
    statut = db.Column(db.Enum('en_attente', 'validee', 'pretee', 'livree', 'annulee', name='statuts_ordonnance'), default='en_attente')
    
    # Relations
    lignes = db.relationship('LigneOrdonnance', backref='ordonnance', lazy=True)

class LigneOrdonnance(db.Model):
    __tablename__ = 'lignes_ordonnance'
    
    id = db.Column(db.Integer, primary_key=True)
    ordonnance_id = db.Column(db.Integer, db.ForeignKey('ordonnances.id'), nullable=False)
    medicament_id = db.Column(db.Integer, db.ForeignKey('medicaments.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    posologie = db.Column(db.Text)
    duree_traitement = db.Column(db.String(50))
    substitutable = db.Column(db.Boolean, default=True)

class Vente(db.Model):
    __tablename__ = 'ventes'
    
    id = db.Column(db.Integer, primary_key=True)
    numero_ticket = db.Column(db.String(50), unique=True, nullable=False)
    date_vente = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'))
    reste_a_payer = db.Column(db.Numeric(10, 2))
    montant_total = db.Column(db.Numeric(10, 2), nullable=False)
    montant_regle = db.Column(db.Numeric(10, 2), nullable=False)
    mode_paiement = db.Column(db.Enum('especes', 'carte', 'cheque', 'virement', 'tiers_payant', name='modes_paiement'), nullable=False)
    informations_paiement = db.Column(db.Text)
    
    # Relations
    lignes = db.relationship('LigneVente', backref='vente', lazy=True)
    historique = db.relationship('HistoriqueVente', backref='vente', lazy=True)

class LigneVente(db.Model):
    __tablename__ = 'lignes_vente'
    
    id = db.Column(db.Integer, primary_key=True)
    vente_id = db.Column(db.Integer, db.ForeignKey('ventes.id'), nullable=False)
    medicament_id = db.Column(db.Integer, db.ForeignKey('medicaments.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False)
    tva = db.Column(db.Numeric(5, 2), nullable=False)
    remise = db.Column(db.Numeric(5, 2), default=0)
    total_ligne = db.Column(db.Numeric(10, 2))

class MouvementStock(db.Model):
    __tablename__ = 'mouvements_stock'
    
    id = db.Column(db.Integer, primary_key=True)
    medicament_id = db.Column(db.Integer, db.ForeignKey('medicaments.id'), nullable=False)
    type_mouvement = db.Column(db.Enum('entree', 'sortie', 'inventaire', 'ajustement', name='types_mouvement'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    date_mouvement = db.Column(db.DateTime, default=datetime.utcnow)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    reference_id = db.Column(db.Integer)
    reference_type = db.Column(db.Enum('achat', 'vente', 'ordonnance', 'inventaire', name='types_reference'))
    notes = db.Column(db.Text)

class Alerte(db.Model):
    __tablename__ = 'alertes'
    
    id = db.Column(db.Integer, primary_key=True)
    type_alerte = db.Column(db.Enum('rupture_stock', 'peremption', 'seuil_minimum', 'interaction', 'autre', name='types_alerte'), nullable=False)
    medicament_id = db.Column(db.Integer, db.ForeignKey('medicaments.id'))
    message = db.Column(db.Text, nullable=False)
    date_creation = db.Column(db.DateTime, default=datetime.utcnow)
    date_resolution = db.Column(db.DateTime)
    statut = db.Column(db.Enum('active', 'resolue', name='statuts_alerte'), default='active')
    priorite = db.Column(db.Enum('basse', 'moyenne', 'haute', 'critique', name='priorites_alerte'), default='moyenne')
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'))

class Proforma(db.Model):
    __tablename__ = 'proformas'
    
    id = db.Column(db.Integer, primary_key=True)
    reference = db.Column(db.String(50), nullable=False)
    client = db.Column(db.String(100), nullable=False)
    montant_total = db.Column(db.Numeric(10, 2), nullable=False)
    date_creation = db.Column(db.DateTime, nullable=False)
    date_validite = db.Column(db.Date, nullable=False)
    createur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    
    # Relations
    details = db.relationship('ProformaDetail', backref='proforma', lazy=True)

class ProformaDetail(db.Model):
    __tablename__ = 'proforma_details'
    
    id = db.Column(db.Integer, primary_key=True)
    proforma_id = db.Column(db.Integer, db.ForeignKey('proformas.id'), nullable=False)
    medicament_id = db.Column(db.Integer, db.ForeignKey('medicaments.id'), nullable=False)
    quantite = db.Column(db.Integer, nullable=False)
    prix_unitaire = db.Column(db.Numeric(10, 2), nullable=False)
    total = db.Column(db.Numeric(10, 2), nullable=False)

class HistoriqueVente(db.Model):
    __tablename__ = 'historique_ventes'
    
    id = db.Column(db.Integer, primary_key=True)
    vente_id = db.Column(db.Integer, db.ForeignKey('ventes.id'), nullable=False)
    action = db.Column(db.Enum('creation', 'modification', 'annulation', name='actions_historique'), nullable=False)
    details = db.Column(db.Text)
    utilisateur_id = db.Column(db.Integer, db.ForeignKey('utilisateurs.id'), nullable=False)
    date_action = db.Column(db.DateTime, default=datetime.utcnow)

class ParametrePharmacie(db.Model):
    __tablename__ = 'parametres_pharmacie'
    
    id = db.Column(db.Integer, primary_key=True)
    nom_pharmacie = db.Column(db.String(100), nullable=False, default='ELM PHARMA')
    adresse_rue = db.Column(db.String(100), nullable=False, default='123 Chaussé de Kasenga bel-air')
    adresse_ville = db.Column(db.String(50), nullable=False, default='Paris')
    adresse_code_postal = db.Column(db.String(20), nullable=False, default='7010')
    adresse_pays = db.Column(db.String(50), nullable=False, default='RD Congo')
    telephone_principal = db.Column(db.String(20), nullable=False, default='01 23 45 67 89')
    telephone_secondaire = db.Column(db.String(20))
    email = db.Column(db.String(100))
    site_web = db.Column(db.String(100))
    rccm = db.Column(db.String(50), comment='Registre du Commerce')
    numero_tva = db.Column(db.String(50), comment='Numéro de TVA intracommunautaire')
    numero_ordre_pharmaciens = db.Column(db.String(50))
    responsable_legal = db.Column(db.String(100), comment='Nom du pharmacien responsable')
    message_accueil_recu = db.Column(db.Text)
    inclure_logo = db.Column(db.Boolean, default=True)
    chemin_logo = db.Column(db.String(255), default='/chemin/vers/logo.png')