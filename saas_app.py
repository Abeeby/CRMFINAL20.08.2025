#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
CRM Elite SAAS - Version complète avec module RH
Architecture multi-tenant avec toutes les fonctionnalités
"""

from flask import Flask, render_template, redirect, url_for, request, jsonify, flash, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, current_user, login_required, login_user, logout_user
from flask_migrate import Migrate
from flask_cors import CORS
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import os
from datetime import datetime, date, timedelta
from werkzeug.security import generate_password_hash, check_password_hash
import stripe
from functools import wraps
import secrets

# Configuration SAAS
class Config:
    # Base config
    SECRET_KEY = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
    
    # Database multi-tenant
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or 'sqlite:///saas_crm.db'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_size': 10,
        'pool_recycle': 3600,
        'pool_pre_ping': True
    }
    
    # Stripe pour la facturation SAAS
    STRIPE_SECRET_KEY = os.environ.get('STRIPE_SECRET_KEY') or 'sk_test_xxx'
    STRIPE_PUBLISHABLE_KEY = os.environ.get('STRIPE_PUBLISHABLE_KEY') or 'pk_test_xxx'
    
    # Plans SAAS
    PLANS = {
        'starter': {
            'name': 'Starter',
            'price': 49,
            'max_users': 5,
            'max_employees': 50,
            'features': ['CRM Base', 'Gestion Employés', 'Pointage', 'Dashboard'],
            'stripe_price_id': 'price_starter'
        },
        'professional': {
            'name': 'Professional',
            'price': 149,
            'max_users': 20,
            'max_employees': 200,
            'features': ['Tout Starter', 'Module RH Complet', 'Paie', 'Formations', 'API'],
            'stripe_price_id': 'price_professional'
        },
        'enterprise': {
            'name': 'Enterprise',
            'price': 499,
            'max_users': -1,  # Illimité
            'max_employees': -1,  # Illimité
            'features': ['Tout Pro', 'Multi-sites', 'Support Premium', 'Personnalisation', 'SSO'],
            'stripe_price_id': 'price_enterprise'
        }
    }
    
    # Security
    SESSION_COOKIE_SECURE = True
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # Rate limiting
    RATELIMIT_STORAGE_URL = "redis://localhost:6379"

# Créer l'application
app = Flask(__name__)
app.config.from_object(Config)

# Extensions
db = SQLAlchemy(app)
migrate = Migrate(app, db)
login_manager = LoginManager(app)
login_manager.login_view = 'auth.login'
cors = CORS(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["1000 per day", "100 per hour"]
)

# Stripe
stripe.api_key = app.config['STRIPE_SECRET_KEY']

# ===== MODÈLES MULTI-TENANT =====

class Tenant(db.Model):
    """Organisation/Entreprise cliente du SAAS"""
    __tablename__ = 'tenants'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(200), nullable=False)
    domain = db.Column(db.String(100), unique=True)  # sous-domaine.crm-elite.com
    slug = db.Column(db.String(100), unique=True, nullable=False)
    plan = db.Column(db.String(50), default='starter')
    stripe_customer_id = db.Column(db.String(200))
    stripe_subscription_id = db.Column(db.String(200))
    status = db.Column(db.String(50), default='trial')  # trial, active, suspended, cancelled
    trial_ends_at = db.Column(db.DateTime)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    settings = db.Column(db.JSON, default={})
    
    # Limites basées sur le plan
    max_users = db.Column(db.Integer, default=5)
    max_employees = db.Column(db.Integer, default=50)
    storage_used = db.Column(db.BigInteger, default=0)  # en bytes
    storage_limit = db.Column(db.BigInteger, default=5*1024*1024*1024)  # 5GB par défaut
    
    # Stats
    users_count = db.Column(db.Integer, default=0)
    employees_count = db.Column(db.Integer, default=0)
    last_activity = db.Column(db.DateTime)
    
    # Relations
    users = db.relationship('User', backref='tenant', lazy='dynamic', cascade='all, delete-orphan')
    employees = db.relationship('Employee', backref='tenant', lazy='dynamic', cascade='all, delete-orphan')

class User(db.Model):
    """Utilisateurs du SAAS (peuvent se connecter)"""
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    email = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(200), nullable=False)
    first_name = db.Column(db.String(100))
    last_name = db.Column(db.String(100))
    role = db.Column(db.String(50), default='user')  # admin, manager, user, hr, accountant
    is_active = db.Column(db.Boolean, default=True)
    is_owner = db.Column(db.Boolean, default=False)  # Propriétaire du tenant
    
    # Permissions RH
    can_manage_hr = db.Column(db.Boolean, default=False)
    can_view_salaries = db.Column(db.Boolean, default=False)
    can_approve_leaves = db.Column(db.Boolean, default=False)
    can_manage_contracts = db.Column(db.Boolean, default=False)
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_login = db.Column(db.DateTime)
    
    # Unique constraint per tenant
    __table_args__ = (db.UniqueConstraint('tenant_id', 'email'),)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)
    
    @property
    def full_name(self):
        return f"{self.first_name} {self.last_name}".strip()

class Employee(db.Model):
    """Employés (module RH)"""
    __tablename__ = 'employees'
    id = db.Column(db.Integer, primary_key=True)
    tenant_id = db.Column(db.Integer, db.ForeignKey('tenants.id'), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'))  # Peut avoir un compte utilisateur
    
    # Informations de base
    employee_id = db.Column(db.String(50), nullable=False)  # ID interne entreprise
    first_name = db.Column(db.String(100), nullable=False)
    last_name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(100))
    position = db.Column(db.String(100))
    hire_date = db.Column(db.Date)
    birth_date = db.Column(db.Date)
    
    # Statut
    is_active = db.Column(db.Boolean, default=True)
    termination_date = db.Column(db.Date)
    
    # Manager
    manager_id = db.Column(db.Integer, db.ForeignKey('employees.id'))
    
    # Unique constraint per tenant
    __table_args__ = (db.UniqueConstraint('tenant_id', 'employee_id'),)

# Import des modèles RH (adaptés pour multi-tenant)
# Tous les modèles RH doivent avoir tenant_id
exec(open('models_rh.py').read())

# ===== MIDDLEWARE MULTI-TENANT =====

def get_current_tenant():
    """Récupère le tenant actuel basé sur le domaine ou la session"""
    if 'tenant_id' in session:
        return Tenant.query.get(session['tenant_id'])
    
    # Récupérer depuis le sous-domaine
    host = request.host.split(':')[0]  # Enlever le port si présent
    subdomain = host.split('.')[0] if '.' in host else None
    
    if subdomain and subdomain != 'www':
        return Tenant.query.filter_by(slug=subdomain).first()
    
    return None

def require_tenant(f):
    """Décorateur pour s'assurer qu'un tenant est sélectionné"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        tenant = get_current_tenant()
        if not tenant:
            return redirect(url_for('select_tenant'))
        return f(*args, **kwargs)
    return decorated_function

def filter_by_tenant(query, model):
    """Filtre automatiquement les requêtes par tenant"""
    tenant = get_current_tenant()
    if tenant and hasattr(model, 'tenant_id'):
        return query.filter(model.tenant_id == tenant.id)
    return query

# ===== ROUTES D'AUTHENTIFICATION =====

@app.route('/')
def index():
    """Page d'accueil du SAAS"""
    return render_template('saas/landing.html', plans=app.config['PLANS'])

@app.route('/register', methods=['GET', 'POST'])
@limiter.limit("5 per hour")
def register():
    """Inscription d'une nouvelle organisation"""
    if request.method == 'POST':
        # Créer le tenant
        tenant = Tenant(
            name=request.form['company_name'],
            slug=request.form['company_name'].lower().replace(' ', '-'),
            plan=request.form.get('plan', 'starter'),
            status='trial',
            trial_ends_at=datetime.now() + timedelta(days=14)
        )
        
        # Appliquer les limites du plan
        plan = app.config['PLANS'][tenant.plan]
        tenant.max_users = plan['max_users']
        tenant.max_employees = plan['max_employees']
        
        db.session.add(tenant)
        db.session.flush()
        
        # Créer l'utilisateur propriétaire
        user = User(
            tenant_id=tenant.id,
            email=request.form['email'],
            first_name=request.form['first_name'],
            last_name=request.form['last_name'],
            role='admin',
            is_owner=True,
            can_manage_hr=True,
            can_view_salaries=True,
            can_approve_leaves=True,
            can_manage_contracts=True
        )
        user.set_password(request.form['password'])
        
        db.session.add(user)
        db.session.commit()
        
        # Créer le client Stripe
        if app.config['STRIPE_SECRET_KEY'] != 'sk_test_xxx':
            customer = stripe.Customer.create(
                email=user.email,
                name=tenant.name,
                metadata={'tenant_id': tenant.id}
            )
            tenant.stripe_customer_id = customer.id
            db.session.commit()
        
        flash(f'Bienvenue ! Votre essai gratuit de 14 jours a commencé.', 'success')
        
        # Auto-login
        login_user(user)
        session['tenant_id'] = tenant.id
        
        return redirect(url_for('dashboard'))
    
    return render_template('saas/register.html', plans=app.config['PLANS'])

@app.route('/login', methods=['GET', 'POST'])
def login():
    """Connexion utilisateur"""
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']
        tenant_slug = request.form.get('tenant')
        
        # Trouver le tenant
        tenant = None
        if tenant_slug:
            tenant = Tenant.query.filter_by(slug=tenant_slug).first()
        
        # Chercher l'utilisateur
        if tenant:
            user = User.query.filter_by(tenant_id=tenant.id, email=email).first()
        else:
            # Recherche globale si pas de tenant spécifié
            user = User.query.filter_by(email=email).first()
            if user:
                tenant = user.tenant
        
        if user and user.check_password(password) and user.is_active:
            # Vérifier le statut du tenant
            if tenant.status == 'suspended':
                flash('Votre compte est suspendu. Veuillez contacter le support.', 'error')
                return redirect(url_for('login'))
            
            login_user(user)
            session['tenant_id'] = tenant.id
            user.last_login = datetime.now()
            tenant.last_activity = datetime.now()
            db.session.commit()
            
            return redirect(url_for('dashboard'))
        
        flash('Email ou mot de passe incorrect', 'error')
    
    return render_template('saas/login.html')

# ===== DASHBOARD PRINCIPAL =====

@app.route('/dashboard')
@login_required
@require_tenant
def dashboard():
    """Dashboard principal avec toutes les métriques"""
    tenant = get_current_tenant()
    
    # Stats générales
    stats = {
        'employees': Employee.query.filter_by(tenant_id=tenant.id, is_active=True).count(),
        'users': User.query.filter_by(tenant_id=tenant.id, is_active=True).count(),
        'clients': 0,  # À implémenter
        'projects': 0,  # À implémenter
    }
    
    # Stats RH
    hr_stats = {
        'absences_today': 0,
        'leaves_pending': DemandeConge.query.filter_by(statut='en_attente').count() if hasattr(DemandeConge, '__tablename__') else 0,
        'contracts_ending': Contrat.query.filter(
            Contrat.date_fin <= date.today() + timedelta(days=30)
        ).count() if hasattr(Contrat, '__tablename__') else 0,
        'trainings_month': 0
    }
    
    # Informations du plan
    plan_info = {
        'name': app.config['PLANS'][tenant.plan]['name'],
        'users_used': tenant.users_count,
        'users_limit': tenant.max_users,
        'employees_used': tenant.employees_count,
        'employees_limit': tenant.max_employees,
        'storage_used_gb': tenant.storage_used / (1024**3),
        'storage_limit_gb': tenant.storage_limit / (1024**3),
        'trial_days_left': (tenant.trial_ends_at - datetime.now()).days if tenant.status == 'trial' else None
    }
    
    return render_template('saas/dashboard.html', 
                         stats=stats, 
                         hr_stats=hr_stats,
                         plan_info=plan_info,
                         tenant=tenant)

# ===== GESTION DU TENANT =====

@app.route('/settings/tenant')
@login_required
@require_tenant
def tenant_settings():
    """Paramètres du tenant"""
    tenant = get_current_tenant()
    
    if not current_user.is_owner and current_user.role != 'admin':
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard'))
    
    return render_template('saas/tenant_settings.html', tenant=tenant, plans=app.config['PLANS'])

@app.route('/settings/billing')
@login_required
@require_tenant
def billing():
    """Gestion de la facturation"""
    tenant = get_current_tenant()
    
    if not current_user.is_owner:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard'))
    
    # Récupérer les informations Stripe
    subscription = None
    invoices = []
    
    if tenant.stripe_subscription_id:
        try:
            subscription = stripe.Subscription.retrieve(tenant.stripe_subscription_id)
            invoices = stripe.Invoice.list(customer=tenant.stripe_customer_id, limit=10)
        except:
            pass
    
    return render_template('saas/billing.html', 
                         tenant=tenant, 
                         subscription=subscription,
                         invoices=invoices,
                         plans=app.config['PLANS'])

@app.route('/upgrade/<plan>')
@login_required
@require_tenant
def upgrade_plan(plan):
    """Upgrade vers un plan supérieur"""
    tenant = get_current_tenant()
    
    if not current_user.is_owner:
        flash('Seul le propriétaire peut changer de plan', 'error')
        return redirect(url_for('billing'))
    
    if plan not in app.config['PLANS']:
        flash('Plan invalide', 'error')
        return redirect(url_for('billing'))
    
    # Créer la session Stripe Checkout
    try:
        checkout_session = stripe.checkout.Session.create(
            customer=tenant.stripe_customer_id,
            payment_method_types=['card'],
            line_items=[{
                'price': app.config['PLANS'][plan]['stripe_price_id'],
                'quantity': 1,
            }],
            mode='subscription',
            success_url=url_for('upgrade_success', _external=True) + '?session_id={CHECKOUT_SESSION_ID}',
            cancel_url=url_for('billing', _external=True),
            metadata={
                'tenant_id': tenant.id,
                'plan': plan
            }
        )
        
        return redirect(checkout_session.url, code=303)
    except Exception as e:
        flash(f'Erreur lors de la mise à niveau : {str(e)}', 'error')
        return redirect(url_for('billing'))

# ===== INTÉGRATION DU MODULE RH =====

# Import des routes RH
from routes_rh import rh_bp
app.register_blueprint(rh_bp)

# Adapter les routes RH pour le multi-tenant
@app.before_request
def inject_tenant():
    """Injecte automatiquement le tenant dans toutes les requêtes"""
    if current_user.is_authenticated:
        g.tenant = get_current_tenant()

# ===== GESTION DES UTILISATEURS =====

@app.route('/users')
@login_required
@require_tenant
def users_list():
    """Liste des utilisateurs du tenant"""
    tenant = get_current_tenant()
    
    if current_user.role not in ['admin', 'manager']:
        flash('Accès non autorisé', 'error')
        return redirect(url_for('dashboard'))
    
    users = User.query.filter_by(tenant_id=tenant.id).all()
    
    return render_template('saas/users.html', users=users, tenant=tenant)

@app.route('/users/invite', methods=['POST'])
@login_required
@require_tenant
def invite_user():
    """Inviter un nouvel utilisateur"""
    tenant = get_current_tenant()
    
    if current_user.role != 'admin':
        return jsonify({'error': 'Non autorisé'}), 403
    
    # Vérifier les limites du plan
    if tenant.users_count >= tenant.max_users and tenant.max_users != -1:
        return jsonify({'error': f'Limite de {tenant.max_users} utilisateurs atteinte. Passez à un plan supérieur.'}), 400
    
    email = request.json['email']
    role = request.json.get('role', 'user')
    
    # Créer l'utilisateur
    user = User(
        tenant_id=tenant.id,
        email=email,
        role=role,
        first_name=request.json.get('first_name'),
        last_name=request.json.get('last_name')
    )
    
    # Générer un mot de passe temporaire
    temp_password = secrets.token_urlsafe(12)
    user.set_password(temp_password)
    
    db.session.add(user)
    tenant.users_count += 1
    db.session.commit()
    
    # TODO: Envoyer un email d'invitation avec le mot de passe temporaire
    
    return jsonify({
        'success': True,
        'message': f'Invitation envoyée à {email}',
        'temp_password': temp_password  # En production, l'envoyer par email uniquement
    })

# ===== API REST =====

@app.route('/api/v1/stats')
@login_required
@require_tenant
def api_stats():
    """API pour récupérer les statistiques"""
    tenant = get_current_tenant()
    
    stats = {
        'tenant': {
            'name': tenant.name,
            'plan': tenant.plan,
            'status': tenant.status,
            'users': tenant.users_count,
            'employees': tenant.employees_count
        },
        'hr': {
            'absences_today': 0,
            'leaves_pending': 0,
            'payroll_month': 0
        },
        'crm': {
            'clients': 0,
            'projects_active': 0,
            'invoices_pending': 0
        }
    }
    
    return jsonify(stats)

@app.route('/api/v1/employees')
@login_required
@require_tenant
def api_employees():
    """API pour la liste des employés"""
    tenant = get_current_tenant()
    
    employees = Employee.query.filter_by(tenant_id=tenant.id, is_active=True).all()
    
    return jsonify([{
        'id': e.id,
        'employee_id': e.employee_id,
        'name': f"{e.first_name} {e.last_name}",
        'department': e.department,
        'position': e.position,
        'email': e.email
    } for e in employees])

# ===== WEBHOOKS =====

@app.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Webhook Stripe pour gérer les événements de paiement"""
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, os.environ.get('STRIPE_WEBHOOK_SECRET')
        )
    except ValueError:
        return '', 400
    except stripe.error.SignatureVerificationError:
        return '', 400
    
    # Gérer les événements
    if event['type'] == 'checkout.session.completed':
        session = event['data']['object']
        tenant_id = session['metadata']['tenant_id']
        plan = session['metadata']['plan']
        
        tenant = Tenant.query.get(tenant_id)
        if tenant:
            tenant.plan = plan
            tenant.status = 'active'
            tenant.stripe_subscription_id = session['subscription']
            
            # Mettre à jour les limites
            plan_config = app.config['PLANS'][plan]
            tenant.max_users = plan_config['max_users']
            tenant.max_employees = plan_config['max_employees']
            
            db.session.commit()
    
    elif event['type'] == 'invoice.payment_failed':
        invoice = event['data']['object']
        customer_id = invoice['customer']
        
        tenant = Tenant.query.filter_by(stripe_customer_id=customer_id).first()
        if tenant:
            tenant.status = 'suspended'
            db.session.commit()
    
    return '', 200

# ===== INITIALISATION =====

@app.before_first_request
def initialize():
    """Initialiser la base de données"""
    db.create_all()
    
    # Créer un tenant de démo si aucun n'existe
    if Tenant.query.count() == 0:
        demo_tenant = Tenant(
            name='Demo Company',
            slug='demo',
            plan='professional',
            status='active'
        )
        db.session.add(demo_tenant)
        db.session.flush()
        
        # Créer un utilisateur admin de démo
        admin = User(
            tenant_id=demo_tenant.id,
            email='admin@demo.com',
            first_name='Admin',
            last_name='Demo',
            role='admin',
            is_owner=True,
            can_manage_hr=True,
            can_view_salaries=True,
            can_approve_leaves=True,
            can_manage_contracts=True
        )
        admin.set_password('demo123')
        db.session.add(admin)
        
        db.session.commit()
        print("✅ Tenant de démo créé : demo.crm-elite.com")
        print("   Email: admin@demo.com")
        print("   Mot de passe: demo123")

# ===== ERROR HANDLERS =====

@app.errorhandler(404)
def not_found(e):
    return render_template('saas/404.html'), 404

@app.errorhandler(500)
def internal_error(e):
    db.session.rollback()
    return render_template('saas/500.html'), 500

@app.errorhandler(429)
def rate_limit_exceeded(e):
    return render_template('saas/429.html', retry_after=e.description), 429

# ===== MAIN =====

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8000))
    app.run(
        host='0.0.0.0',
        port=port,
        debug=os.environ.get('FLASK_ENV') == 'development'
    )