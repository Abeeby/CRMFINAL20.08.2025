#!/usr/bin/env python3
"""
Site Web Premium Globibat - Construction & Rénovation Suisse Romande
Animations GSAP, micro-interactions, design minimal et conversions optimisées
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory, abort
from flask_cors import CORS
from datetime import datetime
import os
import json
from werkzeug.utils import secure_filename
import re

# Configuration Flask
app = Flask(__name__, 
    template_folder='globibat/templates',
    static_folder='globibat/static'
)
app.config['SECRET_KEY'] = 'globibat-premium-2024'
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size
CORS(app)

# Headers de sécurité
@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
    response.headers['Content-Security-Policy'] = "default-src 'self' 'unsafe-inline' 'unsafe-eval' https: data: blob:;"
    return response

# Configuration uploads
UPLOAD_FOLDER = 'globibat/static/uploads'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'webp', 'pdf'}
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# Données des services Globibat
SERVICES = {
    'electricite-depannage': {
        'title': 'Électricité & Dépannage',
        'slug': 'electricite-depannage',
        'icon': 'ri-flashlight-line',
        'description': 'Installations électriques, mises en conformité OIBT, tableaux et circuits, éclairage LED, recherche de panne, interventions rapides 7j/7.',
        'image': 'electricite.jpg',
        'benefits': [
            'Intervention rapide 7j/7',
            'Mise en conformité OIBT',
            'Devis gratuit sous 48h'
        ],
        'price_range': 'Dès 150 CHF/h',
        'zones': ['Nyon', 'District de Nyon', 'Vaud', 'Genève']
    },
    'construction-metallique': {
        'title': 'Construction Métallique',
        'slug': 'construction-metallique',
        'icon': 'ri-tools-line',
        'description': 'Structures sur mesure, soudure professionnelle, réparations, portails, escaliers, garde-corps. Travail du métal de précision.',
        'image': 'metallique.jpg',
        'benefits': [
            'Fabrication sur mesure',
            'Soudure certifiée',
            'Garantie 10 ans'
        ],
        'price_range': 'Sur devis',
        'zones': ['Nyon', 'La Côte', 'Genève']
    },
    'renovation-transformation': {
        'title': 'Rénovation & Transformation',
        'slug': 'renovation-transformation',
        'icon': 'ri-home-heart-line',
        'description': 'Cuisines, salles de bain, cloisonnement, plâtrerie, peinture, sols et carrelage. Transformation complète de votre intérieur.',
        'image': 'renovation.jpg',
        'benefits': [
            'Projet clé en main',
            'Respect des délais',
            'Finitions soignées'
        ],
        'price_range': '800-1500 CHF/m²',
        'zones': ['Nyon', 'Vaud', 'Genève', 'Suisse romande']
    },
    'serrurerie-depannage': {
        'title': 'Serrurerie & Ouverture',
        'slug': 'serrurerie-depannage',
        'icon': 'ri-key-line',
        'description': 'Sécurisation, remplacement de serrures, dépannages urgents, ouverture de portes. Service disponible 24h/24.',
        'image': 'serrurerie.jpg',
        'benefits': [
            'Disponible 24h/24',
            'Intervention < 30min',
            'Toutes marques'
        ],
        'price_range': 'Dès 180 CHF',
        'zones': ['Nyon', 'District de Nyon']
    },
    'nettoyage-conciergerie': {
        'title': 'Nettoyage & Conciergerie',
        'slug': 'nettoyage-conciergerie',
        'icon': 'ri-sparkles-line',
        'description': 'Fin de chantier, fin de bail, entretien régulier. Service professionnel pour particuliers et entreprises.',
        'image': 'nettoyage.jpg',
        'benefits': [
            'Produits écologiques',
            'Équipe formée',
            'Satisfaction garantie'
        ],
        'price_range': 'Dès 35 CHF/h',
        'zones': ['Nyon', 'La Côte', 'Vaud']
    },
    'demenagement-debarras': {
        'title': 'Déménagement & Débarras',
        'slug': 'demenagement-debarras',
        'icon': 'ri-truck-line',
        'description': 'Logements, bureaux, évacuations complètes. Calculateur de volume intégré, recyclage responsable.',
        'image': 'demenagement.jpg',
        'benefits': [
            'Devis immédiat en ligne',
            'Recyclage responsable',
            'Assurance transport'
        ],
        'price_range': 'Dès 80 CHF/m³',
        'zones': ['Suisse romande']
    }
}

# Projets portfolio
PROJECTS = [
    {
        'id': 1,
        'title': 'Villa contemporaine',
        'slug': 'villa-contemporaine-nyon',
        'location': 'Nyon',
        'surface': '280 m²',
        'year': 2024,
        'type': 'Construction neuve',
        'categories': ['construction', 'metal'],
        'duration': '8 mois',
        'budget': '850\'000 CHF',
        'description': 'Construction complète d\'une villa moderne avec structure métallique apparente.',
        'images': ['villa1.jpg', 'villa2.jpg', 'villa3.jpg'],
        'before_after': True,
        'testimonial': 'Travail remarquable, délais respectés et finitions parfaites.',
        'client': 'M. Dubois'
    },
    {
        'id': 2,
        'title': 'Rénovation appartement ancien',
        'slug': 'renovation-appartement-geneve',
        'location': 'Genève',
        'surface': '120 m²',
        'year': 2024,
        'type': 'Rénovation complète',
        'categories': ['renovation', 'electricite'],
        'duration': '3 mois',
        'budget': '180\'000 CHF',
        'description': 'Transformation totale avec mise aux normes électriques et nouvelle cuisine.',
        'images': ['appart1.jpg', 'appart2.jpg', 'appart3.jpg'],
        'before_after': True,
        'testimonial': 'Équipe professionnelle et à l\'écoute. Résultat au-delà de nos attentes.',
        'client': 'Mme Martin'
    },
    {
        'id': 3,
        'title': 'Escalier métallique design',
        'slug': 'escalier-metallique-rolle',
        'location': 'Rolle',
        'surface': '45 m²',
        'year': 2023,
        'type': 'Construction métallique',
        'categories': ['metal'],
        'duration': '3 semaines',
        'budget': '35\'000 CHF',
        'description': 'Fabrication sur mesure d\'un escalier hélicoïdal en acier et verre.',
        'images': ['escalier1.jpg', 'escalier2.jpg', 'escalier3.jpg'],
        'before_after': False,
        'testimonial': 'Un travail d\'orfèvre, précis et élégant.',
        'client': 'Architecte Moreau'
    }
]

# Routes principales
@app.route('/')
def home():
    """Page d'accueil avec toutes les sections"""
    return render_template('home.html',
        services=SERVICES,
        projects=PROJECTS[:3],
        current_year=datetime.now().year
    )

@app.route('/services')
def services_list():
    """Page hub des services"""
    return render_template('services.html',
        services=SERVICES,
        current_year=datetime.now().year
    )

@app.route('/services/<slug>')
def service_detail(slug):
    """Page détaillée d'un service"""
    service = SERVICES.get(slug)
    if not service:
        abort(404)
    
    # Projets liés au service
    related_projects = [p for p in PROJECTS if any(cat in service['slug'].split('-') for cat in p['categories'])]
    
    return render_template('service_detail.html',
        service=service,
        related_projects=related_projects[:2],
        services=SERVICES,
        current_year=datetime.now().year
    )

@app.route('/realisations')
def projects():
    """Portfolio des réalisations"""
    category = request.args.get('category', 'all')
    
    if category != 'all':
        filtered_projects = [p for p in PROJECTS if category in p['categories']]
    else:
        filtered_projects = PROJECTS
    
    return render_template('projects.html',
        projects=filtered_projects,
        selected_category=category,
        current_year=datetime.now().year
    )

@app.route('/realisations/<slug>')
def project_detail(slug):
    """Page détaillée d'un projet"""
    project = next((p for p in PROJECTS if p['slug'] == slug), None)
    if not project:
        abort(404)
    
    return render_template('project_detail.html',
        project=project,
        current_year=datetime.now().year
    )

@app.route('/a-propos')
def about():
    """Page à propos"""
    return render_template('about.html',
        current_year=datetime.now().year
    )

@app.route('/blog')
def blog():
    """Page blog et actualités"""
    return render_template('blog.html',
        current_year=datetime.now().year
    )

@app.route('/devis')
def devis_direct():
    """Redirection vers la page de contact pour le devis"""
    return redirect(url_for('contact'))

@app.route('/contact')
def contact():
    """Page contact avec formulaire multi-étapes"""
    return render_template('contact.html',
        services=SERVICES,
        current_year=datetime.now().year
    )

@app.route('/mentions_legales')
def mentions_legales():
    """Page mentions légales"""
    return render_template('mentions_legales.html',
        current_year=datetime.now().year
    )

@app.route('/politique_confidentialite')
def politique_confidentialite():
    """Page politique de confidentialité"""
    return render_template('politique_confidentialite.html',
        current_year=datetime.now().year
    )

@app.route('/calculateur-de-volume')
def volume_calculator():
    """Calculateur de volume pour déménagement/débarras"""
    return render_template('calculator.html',
        current_year=datetime.now().year
    )

# API endpoints
@app.route('/api/contact', methods=['POST'])
def submit_contact():
    """Traitement du formulaire de contact"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        
        # Gestion des différents formats de champs
        # Support des variantes de noms de champs
        name = data.get('name') or data.get('nom') or ''
        email = data.get('email') or ''
        phone = data.get('phone') or data.get('telephone') or ''
        project_type = data.get('project_type') or data.get('type') or 'Non spécifié'
        
        # Validation basique
        if not name or not email:
            return jsonify({'success': False, 'error': 'Nom et email sont requis'}), 400
        
        # Validation email
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return jsonify({'success': False, 'error': 'Email invalide'}), 400
        
        # Validation téléphone suisse (si fourni)
        if phone:
            phone = re.sub(r'\D', '', phone)
            if len(phone) < 9:
                return jsonify({'success': False, 'error': 'Numéro de téléphone invalide'}), 400
        
        # Génération référence
        reference = f"GLB-{datetime.now().strftime('%Y%m%d')}-{datetime.now().strftime('%H%M%S')}"
        
        # TODO: Envoyer email de confirmation
        # TODO: Sauvegarder en base de données
        
        return jsonify({
            'success': True,
            'message': 'Votre demande a été envoyée avec succès',
            'reference': reference
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/calculate-volume', methods=['POST'])
def calculate_volume():
    """API pour le calculateur de volume"""
    try:
        data = request.get_json()
        
        # Calcul simple du volume
        items = data.get('items', [])
        total_volume = 0
        
        # Volumes standards en m³
        item_volumes = {
            'canape': 2.5,
            'lit_double': 3,
            'lit_simple': 1.5,
            'armoire': 2,
            'table': 1,
            'chaise': 0.2,
            'frigo': 1,
            'machine_laver': 0.8,
            'carton_standard': 0.1,
            'carton_livre': 0.05
        }
        
        for item in items:
            volume = item_volumes.get(item['type'], 0.5) * item.get('quantity', 1)
            total_volume += volume
        
        # Calcul du prix estimé (80 CHF/m³)
        price_estimate = total_volume * 80
        
        return jsonify({
            'success': True,
            'volume': round(total_volume, 2),
            'price_min': round(price_estimate * 0.9, 0),
            'price_max': round(price_estimate * 1.1, 0),
            'message': f'Volume estimé: {total_volume:.1f} m³'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/newsletter', methods=['POST'])
def newsletter_signup():
    """Inscription à la newsletter"""
    try:
        data = request.get_json() if request.is_json else request.form.to_dict()
        email = data.get('email')
        
        if not email or not re.match(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$', email):
            return jsonify({'success': False, 'error': 'Email invalide'}), 400
        
        # TODO: Ajouter à la liste newsletter
        
        return jsonify({
            'success': True,
            'message': 'Inscription réussie! Vous recevrez nos actualités.'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# Redirections vers le CRM
@app.route('/crm')
def redirect_to_crm():
    """Redirection vers le CRM"""
    return redirect('http://localhost:5005/login')

@app.route('/badge')
def redirect_to_badge():
    """Redirection vers le badge mobile"""
    return redirect('http://localhost:5005/employee/badge')

# Gestion des erreurs
@app.errorhandler(404)
def not_found(e):
    return render_template('404.html', current_year=datetime.now().year), 404

@app.errorhandler(500)
def server_error(e):
    return render_template('500.html', current_year=datetime.now().year), 500

# Sitemap
@app.route('/sitemap.xml')
def sitemap():
    """Génération du sitemap XML"""
    pages = []
    
    # Pages statiques
    static_pages = ['', 'services', 'realisations', 'a-propos', 'contact', 'calculateur-de-volume']
    for page in static_pages:
        pages.append({
            'loc': f"https://www.globibat.ch/{page}",
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'changefreq': 'weekly',
            'priority': '1.0' if page == '' else '0.8'
        })
    
    # Services
    for slug in SERVICES.keys():
        pages.append({
            'loc': f"https://www.globibat.ch/services/{slug}",
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'changefreq': 'monthly',
            'priority': '0.7'
        })
    
    # Projets
    for project in PROJECTS:
        pages.append({
            'loc': f"https://www.globibat.ch/realisations/{project['slug']}",
            'lastmod': datetime.now().strftime('%Y-%m-%d'),
            'changefreq': 'monthly',
            'priority': '0.6'
        })
    
    sitemap_xml = render_template('sitemap.xml', pages=pages)
    response = app.make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

# Robots.txt
@app.route('/robots.txt')
def robots():
    return send_from_directory(app.static_folder, 'robots.txt')

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════╗
║        🏗️  GLOBIBAT - SITE WEB PREMIUM                    ║
║        Construction & Rénovation Suisse Romande          ║
╚══════════════════════════════════════════════════════════╝
    
🌐 Site accessible sur: http://localhost:5000
📱 Téléphone: +41 21 505 00 62
📧 Email: info@globibat.com
📍 Zone: Nyon • Vaud • Genève • Suisse romande

✨ Fonctionnalités:
   • Animations GSAP premium
   • Portfolio avec avant/après
   • Formulaire multi-étapes
   • Calculateur de volume
   • SEO optimisé
   • 100% responsive
    """)
    
    app.run(debug=True, port=5000, host='0.0.0.0')
