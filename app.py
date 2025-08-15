#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Globibat CRM - Version Finale
Application complète avec UI/UX moderne et toutes les fonctionnalités
"""

from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, session, send_file
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, AnonymousUserMixin, login_required, login_user, logout_user, UserMixin
from flask_socketio import SocketIO, emit, join_room, leave_room
from flask_cors import CORS
import os
import sys
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
from functools import wraps
import io
from reportlab.lib.pagesizes import letter, A4
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch

# Configuration
class Config:
    base_dir = os.path.dirname(os.path.abspath(__file__))
    instance_dir = os.path.join(base_dir, 'instance')
    os.makedirs(instance_dir, exist_ok=True)
    
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'globibat-crm-2025-secure-key'
    SQLALCHEMY_DATABASE_URI = 'sqlite:///' + os.path.join(instance_dir, 'globibat_final.db').replace('\\', '/')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# Créer l'application
app = Flask(__name__,
    template_folder='app/templates',
    static_folder='app/static'
)
app.config.from_object(Config)

# Initialiser les extensions
db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
CORS(app)

# ===== MODÈLES =====

class Admin(UserMixin, db.Model):
    __tablename__ = 'admin'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Employe(db.Model):
    __tablename__ = 'employe'
    id = db.Column(db.Integer, primary_key=True)
    matricule = db.Column(db.String(50), unique=True, nullable=False)
    nom = db.Column(db.String(100), nullable=False)
    prenom = db.Column(db.String(100), nullable=False)
    departement = db.Column(db.String(100))
    position = db.Column(db.String(100))
    email = db.Column(db.String(120))
    telephone = db.Column(db.String(20))
    date_embauche = db.Column(db.Date, default=date.today)
    actif = db.Column(db.Boolean, default=True)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    derniere_localisation = db.Column(db.DateTime)
    photo = db.Column(db.String(200))

class Pointage(db.Model):
    __tablename__ = 'pointage'
    id = db.Column(db.Integer, primary_key=True)
    employe_id = db.Column(db.Integer, db.ForeignKey('employe.id'), nullable=False)
    date_pointage = db.Column(db.Date, nullable=False)
    arrivee_matin = db.Column(db.DateTime)
    depart_midi = db.Column(db.DateTime)
    arrivee_apres_midi = db.Column(db.DateTime)
    depart_soir = db.Column(db.DateTime)
    heures_travaillees = db.Column(db.Float, default=0)
    heures_supplementaires = db.Column(db.Float, default=0)
    retard_matin = db.Column(db.Boolean, default=False)
    retard_apres_midi = db.Column(db.Boolean, default=False)
    employe = db.relationship('Employe', backref='pointages')

class Client(db.Model):
    __tablename__ = 'client'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    type_client = db.Column(db.String(50))
    contact = db.Column(db.String(100))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    adresse = db.Column(db.Text)
    ville = db.Column(db.String(100))
    code_postal = db.Column(db.String(10))
    date_creation = db.Column(db.Date, default=date.today)
    actif = db.Column(db.Boolean, default=True)
    notes = db.Column(db.Text)

class Chantier(db.Model):
    __tablename__ = 'chantier'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    adresse = db.Column(db.Text)
    date_debut = db.Column(db.Date)
    date_fin_prevue = db.Column(db.Date)
    date_fin_reelle = db.Column(db.Date)
    statut = db.Column(db.String(50), default='planifie')
    budget_initial = db.Column(db.Float, default=0)
    budget_consomme = db.Column(db.Float, default=0)
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)
    description = db.Column(db.Text)
    chef_chantier_id = db.Column(db.Integer, db.ForeignKey('employe.id'))
    client = db.relationship('Client', backref='chantiers')
    chef_chantier = db.relationship('Employe', backref='chantiers_diriges')

class Devis(db.Model):
    __tablename__ = 'devis'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    date_devis = db.Column(db.Date, default=date.today)
    date_validite = db.Column(db.Date)
    montant_ht = db.Column(db.Float, default=0)
    tva = db.Column(db.Float, default=0)
    montant_ttc = db.Column(db.Float, default=0)
    statut = db.Column(db.String(50), default='brouillon')
    description = db.Column(db.Text)
    conditions = db.Column(db.Text)
    client = db.relationship('Client', backref='devis')

class Facture(db.Model):
    __tablename__ = 'facture'
    id = db.Column(db.Integer, primary_key=True)
    numero = db.Column(db.String(50), unique=True, nullable=False)
    client_id = db.Column(db.Integer, db.ForeignKey('client.id'))
    chantier_id = db.Column(db.Integer, db.ForeignKey('chantier.id'))
    devis_id = db.Column(db.Integer, db.ForeignKey('devis.id'))
    date_facture = db.Column(db.Date, default=date.today)
    date_echeance = db.Column(db.Date)
    montant_ht = db.Column(db.Float, default=0)
    tva = db.Column(db.Float, default=0)
    montant_ttc = db.Column(db.Float, default=0)
    statut = db.Column(db.String(50), default='brouillon')
    client = db.relationship('Client', backref='factures')
    chantier = db.relationship('Chantier', backref='factures')
    devis_ref = db.relationship('Devis', backref='factures')

class Lead(db.Model):
    __tablename__ = 'lead'
    id = db.Column(db.Integer, primary_key=True)
    nom = db.Column(db.String(200), nullable=False)
    entreprise = db.Column(db.String(200))
    telephone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    source = db.Column(db.String(50))
    statut = db.Column(db.String(50), default='nouveau')
    date_creation = db.Column(db.Date, default=date.today)
    date_dernier_contact = db.Column(db.Date)
    notes = db.Column(db.Text)
    potentiel_ca = db.Column(db.Float)
    probabilite = db.Column(db.Integer, default=50)

# User loader
@login_manager.user_loader
def load_user(user_id):
    return Admin.query.get(int(user_id))

# Classe pour utilisateur anonyme
class AnonymousUser(AnonymousUserMixin):
    def __init__(self):
        self.username = 'Invité'
        self.email = ''

login_manager.anonymous_user = AnonymousUser

# Context processor
@app.context_processor
def inject_user():
    return dict(current_user=current_user)

# ===== ROUTES PRINCIPALES =====

@app.route('/')
def index():
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form.get('email')
        password = request.form.get('password')
        
        admin = Admin.query.filter_by(email=email).first()
        if admin and admin.check_password(password):
            login_user(admin, remember=True)
            flash('Connexion réussie', 'success')
            next_page = request.args.get('next')
            return redirect(next_page) if next_page else redirect(url_for('dashboard'))
        else:
            flash('Email ou mot de passe incorrect', 'error')
    
    return render_template('login_final.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Vous avez été déconnecté', 'info')
    return redirect(url_for('login'))

@app.route('/dashboard')
@login_required
def dashboard():
    # Statistiques
    stats = {
        'nb_employes': Employe.query.filter_by(actif=True).count(),
        'nb_clients': Client.query.filter_by(actif=True).count(),
        'chantiers_actifs': Chantier.query.filter_by(statut='en_cours').count(),
        'leads_nouveaux': Lead.query.filter_by(statut='nouveau').count(),
        'factures_impayees': Facture.query.filter(Facture.statut.in_(['envoyee', 'retard'])).count()
    }
    
    # Pointages du jour
    aujourd_hui = date.today()
    pointages_jour = db.session.query(Pointage, Employe).join(Employe).filter(
        Pointage.date_pointage == aujourd_hui
    ).all()
    
    # Chantiers récents
    chantiers_recents = Chantier.query.filter_by(statut='en_cours').order_by(
        Chantier.date_debut.desc()
    ).limit(5).all()
    
    # Factures récentes
    factures_recentes = db.session.query(Facture, Client).join(Client).order_by(
        Facture.date_facture.desc()
    ).limit(5).all()
    
    return render_template('dashboard_elite.html',
                         stats=stats,
                         pointages_jour=pointages_jour,
                         chantiers_recents=chantiers_recents,
                         factures_recentes=factures_recentes,
                         aujourd_hui=aujourd_hui)

@app.route('/employes')
@login_required
def employes():
    employes = Employe.query.order_by(Employe.nom).all()
    departements = db.session.query(Employe.departement).distinct().all()
    return render_template('employes_final.html', 
                         employes=employes,
                         departements=[d[0] for d in departements if d[0]])

@app.route('/clients')
@login_required
def clients():
    clients = Client.query.order_by(Client.nom).all()
    return render_template('clients_final.html', clients=clients)

@app.route('/chantiers')
@login_required
def chantiers():
    chantiers = Chantier.query.order_by(Chantier.date_debut.desc()).all()
    clients = Client.query.filter_by(actif=True).all()
    chefs = Employe.query.filter_by(actif=True, departement='Construction').all()
    return render_template('chantiers_final.html', 
                         chantiers=chantiers,
                         clients=clients,
                         chefs=chefs)

@app.route('/devis')
@login_required
def devis():
    devis_list = Devis.query.order_by(Devis.date_devis.desc()).all()
    clients = Client.query.filter_by(actif=True).all()
    return render_template('devis_final.html', 
                         devis_list=devis_list, 
                         clients=clients)

@app.route('/factures')
@login_required
def factures():
    factures = Facture.query.order_by(Facture.date_facture.desc()).all()
    clients = Client.query.filter_by(actif=True).all()
    chantiers = Chantier.query.all()
    return render_template('factures_final.html', 
                         factures=factures, 
                         clients=clients, 
                         chantiers=chantiers)

@app.route('/leads')
@login_required
def leads():
    leads = Lead.query.order_by(Lead.date_creation.desc()).all()
    return render_template('leads_final.html', leads=leads)

@app.route('/badges')
@login_required
def badges():
    aujourd_hui = date.today()
    pointages = db.session.query(Pointage, Employe).join(Employe).filter(
        Pointage.date_pointage == aujourd_hui
    ).all()
    
    employes_actifs = Employe.query.filter_by(actif=True).all()
    employes_badges = [p.employe_id for p, e in pointages]
    absents = [e for e in employes_actifs if e.id not in employes_badges]
    
    return render_template('badges_final.html',
                         pointages=pointages,
                         absents=absents,
                         aujourd_hui=aujourd_hui)

@app.route('/carte')
@login_required
def carte():
    chantiers = Chantier.query.filter(Chantier.latitude.isnot(None)).all()
    employes = Employe.query.filter(
        Employe.latitude.isnot(None),
        Employe.actif == True
    ).all()
    return render_template('carte_final.html', 
                         chantiers=chantiers, 
                         employes=employes)

@app.route('/parametres')
@login_required
def parametres():
    return render_template('parametres_final.html')

# ===== SYSTÈME DE BADGE EMPLOYÉS =====

@app.route('/employee/badge')
def badge_employee():
    """Interface de badge pour les employés (sans authentification requise)"""
    return render_template('badge_mobile_elite.html')

@app.route('/api/badge/check', methods=['POST'])
def badge_check():
    """Enregistrer un pointage via matricule"""
    try:
        data = request.json
        matricule = data.get('matricule')
        latitude = data.get('latitude')
        longitude = data.get('longitude')
        
        if not matricule:
            return jsonify({
                'success': False,
                'message': 'Matricule requis'
            }), 400
        
        # Trouver l'employé
        employe = Employe.query.filter_by(matricule=matricule, actif=True).first()
        
        if not employe:
            return jsonify({
                'success': False,
                'message': 'Matricule invalide ou employé inactif'
            }), 404
        
        # Mettre à jour la géolocalisation
        if latitude and longitude:
            employe.latitude = latitude
            employe.longitude = longitude
            employe.derniere_localisation = datetime.now()
        
        # Logique de pointage
        aujourd_hui = date.today()
        pointage = Pointage.query.filter_by(
            employe_id=employe.id,
            date_pointage=aujourd_hui
        ).first()
        
        if not pointage:
            pointage = Pointage(
                employe_id=employe.id,
                date_pointage=aujourd_hui
            )
            db.session.add(pointage)
        
        maintenant = datetime.now()
        action_type = None
        message = ""
        
        if not pointage.arrivee_matin:
            pointage.arrivee_matin = maintenant
            if maintenant.time() > datetime.strptime('09:00', '%H:%M').time():
                pointage.retard_matin = True
            action_type = "arrivee_matin"
            message = f"Bonjour {employe.prenom}! Arrivée enregistrée à {maintenant.strftime('%H:%M')}"
        elif not pointage.depart_midi:
            pointage.depart_midi = maintenant
            action_type = "depart_midi"
            message = f"Bon appétit {employe.prenom}! Départ midi enregistré à {maintenant.strftime('%H:%M')}"
        elif not pointage.arrivee_apres_midi:
            pointage.arrivee_apres_midi = maintenant
            if maintenant.time() > datetime.strptime('14:00', '%H:%M').time():
                pointage.retard_apres_midi = True
            action_type = "arrivee_apres_midi"
            message = f"Bon retour {employe.prenom}! Retour enregistré à {maintenant.strftime('%H:%M')}"
        elif not pointage.depart_soir:
            pointage.depart_soir = maintenant
            action_type = "depart_soir"
            
            # Calculer les heures
            heures_matin = 0
            heures_apres_midi = 0
            
            if pointage.arrivee_matin and pointage.depart_midi:
                delta_matin = pointage.depart_midi - pointage.arrivee_matin
                heures_matin = delta_matin.total_seconds() / 3600
            
            if pointage.arrivee_apres_midi and pointage.depart_soir:
                delta_apres_midi = pointage.depart_soir - pointage.arrivee_apres_midi
                heures_apres_midi = delta_apres_midi.total_seconds() / 3600
            
            total_heures = round(heures_matin + heures_apres_midi, 2)
            pointage.heures_travaillees = total_heures
            
            if total_heures > 8:
                pointage.heures_supplementaires = round(total_heures - 8, 2)
            
            message = f"Bonne soirée {employe.prenom}! Départ enregistré à {maintenant.strftime('%H:%M')}. Total: {total_heures}h"
        else:
            return jsonify({
                'success': False,
                'message': 'Tous les pointages du jour sont déjà enregistrés'
            }), 400
        
        db.session.commit()
        
        # Émettre l'événement WebSocket
        socketio.emit('badge_update', {
            'employe': f'{employe.prenom} {employe.nom}',
            'matricule': employe.matricule,
            'type': action_type,
            'heure': maintenant.strftime('%H:%M'),
            'timestamp': maintenant.isoformat()
        })
        
        return jsonify({
            'success': True,
            'message': message,
            'action_type': action_type,
            'employee': {
                'name': f"{employe.prenom} {employe.nom}",
                'position': employe.position,
                'department': employe.departement,
                'photo': employe.photo
            }
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({
            'success': False,
            'message': f'Erreur lors du pointage: {str(e)}'
        }), 500

# ===== API ENDPOINTS =====

@app.route('/api/employes', methods=['GET', 'POST'])
@login_required
def api_employes():
    if request.method == 'GET':
        employes = Employe.query.all()
        return jsonify([{
            'id': e.id,
            'matricule': e.matricule,
            'nom': e.nom,
            'prenom': e.prenom,
            'departement': e.departement,
            'position': e.position,
            'email': e.email,
            'telephone': e.telephone,
            'actif': e.actif
        } for e in employes])
    
    elif request.method == 'POST':
        data = request.json
        
        # Générer matricule automatique
        count = Employe.query.count() + 1
        matricule = f"EMP{count:03d}"
        
        employe = Employe(
            matricule=matricule,
            nom=data['nom'],
            prenom=data['prenom'],
            departement=data.get('departement'),
            position=data.get('position'),
            email=data.get('email'),
            telephone=data.get('telephone')
        )
        db.session.add(employe)
        db.session.commit()
        
        return jsonify({'success': True, 'id': employe.id, 'matricule': matricule})

@app.route('/api/employes/<int:id>', methods=['PUT', 'DELETE'])
@login_required
def api_employe_detail(id):
    employe = Employe.query.get_or_404(id)
    
    if request.method == 'PUT':
        data = request.json
        employe.nom = data.get('nom', employe.nom)
        employe.prenom = data.get('prenom', employe.prenom)
        employe.departement = data.get('departement', employe.departement)
        employe.position = data.get('position', employe.position)
        employe.email = data.get('email', employe.email)
        employe.telephone = data.get('telephone', employe.telephone)
        db.session.commit()
        return jsonify({'success': True})
    
    elif request.method == 'DELETE':
        employe.actif = False
        db.session.commit()
        return jsonify({'success': True})

@app.route('/api/clients', methods=['GET', 'POST'])
@login_required
def api_clients():
    if request.method == 'GET':
        clients = Client.query.all()
        return jsonify([{
            'id': c.id,
            'nom': c.nom,
            'type_client': c.type_client,
            'contact': c.contact,
            'telephone': c.telephone,
            'email': c.email,
            'ville': c.ville,
            'actif': c.actif
        } for c in clients])
    
    elif request.method == 'POST':
        data = request.json
        client = Client(
            nom=data['nom'],
            type_client=data.get('type_client', 'particulier'),
            contact=data.get('contact'),
            telephone=data.get('telephone'),
            email=data.get('email'),
            adresse=data.get('adresse'),
            ville=data.get('ville'),
            code_postal=data.get('code_postal'),
            notes=data.get('notes')
        )
        db.session.add(client)
        db.session.commit()
        return jsonify({'success': True, 'id': client.id})

@app.route('/api/devis', methods=['POST'])
@login_required
def api_create_devis():
    data = request.json
    
    # Générer numéro de devis
    count = Devis.query.count() + 1
    numero = f"DEV-{datetime.now().year}-{count:04d}"
    
    devis = Devis(
        numero=numero,
        client_id=data['client_id'],
        montant_ht=float(data.get('montant_ht', 0)),
        tva=float(data.get('tva', 0)),
        montant_ttc=float(data.get('montant_ttc', 0)),
        description=data.get('description'),
        conditions=data.get('conditions'),
        date_validite=datetime.strptime(data['date_validite'], '%Y-%m-%d').date() if data.get('date_validite') else None
    )
    db.session.add(devis)
    db.session.commit()
    
    return jsonify({'success': True, 'id': devis.id, 'numero': devis.numero})

@app.route('/api/factures', methods=['POST'])
@login_required
def api_create_facture():
    data = request.json
    
    # Générer numéro de facture
    count = Facture.query.count() + 1
    numero = f"FAC-{datetime.now().year}-{count:04d}"
    
    facture = Facture(
        numero=numero,
        client_id=data['client_id'],
        chantier_id=data.get('chantier_id'),
        devis_id=data.get('devis_id'),
        montant_ht=float(data.get('montant_ht', 0)),
        tva=float(data.get('tva', 0)),
        montant_ttc=float(data.get('montant_ttc', 0)),
        date_echeance=datetime.strptime(data['date_echeance'], '%Y-%m-%d').date() if data.get('date_echeance') else None
    )
    db.session.add(facture)
    db.session.commit()
    
    return jsonify({'success': True, 'id': facture.id, 'numero': facture.numero})

@app.route('/api/leads', methods=['POST'])
@login_required
def api_create_lead():
    data = request.json
    
    lead = Lead(
        nom=data['nom'],
        entreprise=data.get('entreprise'),
        telephone=data.get('telephone'),
        email=data.get('email'),
        source=data.get('source', 'site_web'),
        notes=data.get('notes'),
        potentiel_ca=float(data.get('potentiel_ca', 0)),
        probabilite=int(data.get('probabilite', 50))
    )
    db.session.add(lead)
    db.session.commit()
    
    return jsonify({'success': True, 'id': lead.id})

@app.route('/api/stats/dashboard')
@login_required
def api_dashboard_stats():
    stats = {
        'employes_actifs': Employe.query.filter_by(actif=True).count(),
        'clients_actifs': Client.query.filter_by(actif=True).count(),
        'chantiers_en_cours': Chantier.query.filter_by(statut='en_cours').count(),
        'leads_nouveaux': Lead.query.filter_by(statut='nouveau').count(),
        'factures_impayees': Facture.query.filter(Facture.statut.in_(['envoyee', 'retard'])).count(),
        'ca_mois': db.session.query(db.func.sum(Facture.montant_ttc)).filter(
            Facture.date_facture >= date.today().replace(day=1),
            Facture.statut == 'payee'
        ).scalar() or 0
    }
    return jsonify(stats)

# ===== GÉNÉRATION PDF =====

@app.route('/api/devis/<int:id>/pdf')
@login_required
def devis_pdf(id):
    devis = Devis.query.get_or_404(id)
    
    # Créer le PDF
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    
    # En-tête
    p.setFont("Helvetica-Bold", 20)
    p.drawString(50, height - 50, "GLOBIBAT")
    p.setFont("Helvetica", 10)
    p.drawString(50, height - 70, "Entreprise de construction générale")
    p.drawString(50, height - 85, "Tél: 05 61 00 00 00 - Email: info@globibat.com")
    
    # Titre
    p.setFont("Helvetica-Bold", 16)
    p.drawString(50, height - 150, f"DEVIS N° {devis.numero}")
    
    # Infos client
    p.setFont("Helvetica", 12)
    p.drawString(350, height - 150, f"Date: {devis.date_devis.strftime('%d/%m/%Y')}")
    if devis.date_validite:
        p.drawString(350, height - 170, f"Validité: {devis.date_validite.strftime('%d/%m/%Y')}")
    
    if devis.client:
        p.drawString(50, height - 200, "CLIENT:")
        p.drawString(50, height - 220, devis.client.nom)
        if devis.client.adresse:
            p.drawString(50, height - 240, devis.client.adresse)
        if devis.client.ville:
            p.drawString(50, height - 260, f"{devis.client.code_postal} {devis.client.ville}")
    
    # Description
    if devis.description:
        p.drawString(50, height - 320, "DESCRIPTION:")
        y = height - 340
        for line in devis.description.split('\n'):
            p.drawString(50, y, line[:80])
            y -= 20
    
    # Montants
    y = height - 500
    p.line(50, y, width - 50, y)
    y -= 30
    p.drawString(350, y, f"Montant HT: {devis.montant_ht:.2f} €")
    y -= 20
    p.drawString(350, y, f"TVA (20%): {devis.tva:.2f} €")
    y -= 20
    p.setFont("Helvetica-Bold", 12)
    p.drawString(350, y, f"TOTAL TTC: {devis.montant_ttc:.2f} €")
    
    # Conditions
    if devis.conditions:
        p.setFont("Helvetica", 10)
        p.drawString(50, 100, "Conditions:")
        p.drawString(50, 80, devis.conditions[:100])
    
    p.showPage()
    p.save()
    
    buffer.seek(0)
    return send_file(buffer, 
                     mimetype='application/pdf',
                     as_attachment=True,
                     download_name=f'devis_{devis.numero}.pdf')

# ===== WEBSOCKET EVENTS =====

@socketio.on('connect')
def handle_connect():
    print(f'Client connecté: {request.sid}')
    emit('connected', {'message': 'Connexion établie'})

@socketio.on('disconnect')
def handle_disconnect():
    print(f'Client déconnecté: {request.sid}')

@socketio.on('join_chantier')
def on_join_chantier(data):
    chantier_id = data['chantier_id']
    username = data.get('username', 'Anonyme')
    room = f'chantier_{chantier_id}'
    join_room(room)
    
    emit('system_message', {
        'message': f'{username} a rejoint le chat',
        'timestamp': datetime.now().isoformat()
    }, room=room)

@socketio.on('send_message')
def handle_message(data):
    chantier_id = data['chantier_id']
    room = f'chantier_{chantier_id}'
    
    emit('new_message', {
        'user': data.get('user', 'Anonyme'),
        'message': data['message'],
        'timestamp': datetime.now().isoformat()
    }, room=room)

@socketio.on('send_notification')
def handle_notification(data):
    emit('new_notification', {
        'type': data.get('type', 'info'),
        'title': data.get('title', 'Notification'),
        'message': data['message'],
        'timestamp': datetime.now().isoformat()
    }, broadcast=True)

# ===== INITIALISATION =====

def init_db():
    with app.app_context():
        # Supprimer et recréer les tables
        db.drop_all()
        db.create_all()
        
        # Créer l'admin principal
        admin = Admin(
            username='admin',
            email='info@globibat.com'
        )
        admin.set_password('Miser1597532684$')
        db.session.add(admin)
        
        # Ajouter des employés de test
        employes = [
            Employe(matricule='EMP001', nom='Dupont', prenom='Jean', departement='Construction', 
                   position='Chef de chantier', email='j.dupont@globibat.com', telephone='0612345678'),
            Employe(matricule='EMP002', nom='Martin', prenom='Marie', departement='Administration', 
                   position='Secrétaire', email='m.martin@globibat.com', telephone='0623456789'),
            Employe(matricule='EMP003', nom='Bernard', prenom='Pierre', departement='Construction', 
                   position='Maçon', email='p.bernard@globibat.com', telephone='0634567890'),
            Employe(matricule='EMP004', nom='Durand', prenom='Sophie', departement='Logistique', 
                   position='Responsable', email='s.durand@globibat.com', telephone='0645678901'),
            Employe(matricule='EMP005', nom='Moreau', prenom='Luc', departement='Construction', 
                   position='Électricien', email='l.moreau@globibat.com', telephone='0656789012'),
        ]
        for emp in employes:
            db.session.add(emp)
        
        # Ajouter des clients
        clients = [
            Client(nom='Mairie de Toulouse', type_client='collectivite', contact='Service Travaux',
                  telephone='0561223344', email='travaux@mairie-toulouse.fr', 
                  adresse='Place du Capitole', ville='Toulouse', code_postal='31000'),
            Client(nom='SARL Construction Plus', type_client='entreprise', contact='M. Dupont',
                  telephone='0561334455', email='contact@constructionplus.fr',
                  adresse='12 rue de l\'Industrie', ville='Blagnac', code_postal='31700'),
            Client(nom='M. et Mme Martinez', type_client='particulier', contact='M. Martinez',
                  telephone='0677889900', email='martinez@email.com',
                  adresse='45 avenue des Roses', ville='Colomiers', code_postal='31770'),
        ]
        for client in clients:
            db.session.add(client)
        
        # Ajouter des chantiers
        chantiers = [
            Chantier(
                nom='Rénovation Mairie - Salle des fêtes',
                client_id=1,
                chef_chantier_id=1,
                adresse='Place du Capitole, Toulouse',
                date_debut=date.today() - timedelta(days=30),
                date_fin_prevue=date.today() + timedelta(days=60),
                statut='en_cours',
                budget_initial=250000,
                budget_consomme=87000,
                latitude=43.6047,
                longitude=1.4442,
                description='Rénovation complète de la salle des fêtes municipale'
            ),
            Chantier(
                nom='Construction Villa Martinez',
                client_id=3,
                chef_chantier_id=1,
                adresse='45 avenue des Roses, Colomiers',
                date_debut=date.today() + timedelta(days=15),
                date_fin_prevue=date.today() + timedelta(days=120),
                statut='planifie',
                budget_initial=180000,
                latitude=43.6118,
                longitude=1.3369,
                description='Construction d\'une villa individuelle de 150m²'
            ),
        ]
        for chantier in chantiers:
            db.session.add(chantier)
        
        # Ajouter des leads
        leads = [
            Lead(nom='M. Dubois', entreprise='Dubois Immobilier', telephone='0656789012',
                email='contact@dubois-immo.fr', source='site_web', potentiel_ca=150000, probabilite=70),
            Lead(nom='Mme Petit', telephone='0623456789', email='petit.marie@email.com',
                source='telephone', statut='contacte', potentiel_ca=85000, probabilite=50),
            Lead(nom='SCI Les Jardins', entreprise='SCI Les Jardins', email='contact@jardins.fr',
                source='salon', potentiel_ca=320000, probabilite=30),
        ]
        for lead in leads:
            db.session.add(lead)
        
        # Ajouter des devis
        devis = [
            Devis(
                numero='DEV-2025-0001',
                client_id=2,
                montant_ht=45000,
                tva=9000,
                montant_ttc=54000,
                statut='envoye',
                description='Extension bureau 50m²',
                date_validite=date.today() + timedelta(days=30)
            ),
        ]
        for d in devis:
            db.session.add(d)
        
        # Ajouter des factures
        factures = [
            Facture(
                numero='FAC-2025-0001',
                client_id=1,
                chantier_id=1,
                montant_ht=50000,
                tva=10000,
                montant_ttc=60000,
                statut='payee',
                date_echeance=date.today() - timedelta(days=15)
            ),
            Facture(
                numero='FAC-2025-0002',
                client_id=2,
                montant_ht=15000,
                tva=3000,
                montant_ttc=18000,
                statut='envoyee',
                date_echeance=date.today() + timedelta(days=15)
            ),
        ]
        for facture in factures:
            db.session.add(facture)
        
        # Ajouter des pointages pour aujourd'hui
        aujourd_hui = date.today()
        maintenant = datetime.now()
        
        for i in range(3):
            pointage = Pointage(
                employe_id=i+1,
                date_pointage=aujourd_hui,
                arrivee_matin=maintenant.replace(hour=8, minute=i*5),
                depart_midi=maintenant.replace(hour=12, minute=0),
                arrivee_apres_midi=maintenant.replace(hour=14, minute=i*3),
                heures_travaillees=7.5,
                retard_matin=(i == 2)
            )
            db.session.add(pointage)
        
        db.session.commit()
        print("✅ Base de données initialisée avec succès")

# ===== LANCEMENT =====

if __name__ == '__main__':
    print("\n" + "="*50)
    print("🏗️  GLOBIBAT CRM - VERSION FINALE")
    print("="*50)
    
    init_db()
    
    print("\n📍 URLs d'accès:")
    print("   CRM Principal: http://localhost:5005/login")
    print("   Badge Employés: http://localhost:5005/employee/badge")
    print("\n🔐 Connexion:")
    print("   Email: info@globibat.com")
    print("   Mot de passe: Miser1597532684$")
    print("="*50 + "\n")
    
    socketio.run(app, debug=True, host='0.0.0.0', port=5005)
