#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Site Web Globibat - Application Flask Premium
Site vitrine haut de gamme avec SEO optimisé et animations GSAP
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, send_from_directory
# from flask_sitemap import Sitemap  # Commenté temporairement
import os
from datetime import datetime
import json

# Configuration
website = Flask(__name__, 
    template_folder='website/templates',
    static_folder='website/static'
)
website.config['SECRET_KEY'] = 'globibat-website-2024-premium'
website.config['SITEMAP_INCLUDE_RULES_WITHOUT_PARAMS'] = True

# Initialisation Sitemap pour SEO
# ext = Sitemap(website)  # Commenté temporairement

# Données des services
SERVICES = {
    'renovation-interieure': {
        'title': 'Rénovation Intérieure',
        'meta_title': 'Rénovation Intérieure Genève | Globibat - Expert BTP Premium',
        'meta_description': 'Rénovation intérieure haut de gamme à Genève et Suisse romande. Transformation complète, finitions premium. Devis gratuit sous 48h.',
        'slug': 'renovation-interieure',
        'icon': 'home-heart-line',
        'description': 'Transformez votre intérieur avec notre expertise en rénovation premium',
        'features': [
            'Cuisine et salle de bain',
            'Revêtements sols et murs',
            'Aménagement sur mesure',
            'Domotique intégrée'
        ],
        'price_range': '50\'000 - 500\'000 CHF'
    },
    'isolation-thermique': {
        'title': 'Isolation Thermique',
        'meta_title': 'Isolation Thermique Genève 2026 | Économies Énergie Garanties',
        'meta_description': 'Isolation thermique performante à Genève. Réduisez vos factures de 40%. Aides cantonales disponibles. Certification Minergie.',
        'slug': 'isolation-thermique',
        'icon': 'temp-cold-line',
        'description': 'Solutions d\'isolation haute performance pour économies d\'énergie maximales',
        'features': [
            'Isolation façades ITE',
            'Isolation toiture',
            'Isolation phonique',
            'Certification énergétique'
        ],
        'price_range': '30\'000 - 150\'000 CHF'
    },
    'construction-neuve': {
        'title': 'Construction Neuve',
        'meta_title': 'Construction Maison Neuve Genève | Architecte & Constructeur',
        'meta_description': 'Construction de maisons neuves clé en main à Genève et Lausanne. Villa moderne, écologique. Garantie décennale.',
        'slug': 'construction-neuve',
        'icon': 'building-line',
        'description': 'Réalisation de projets neufs clé en main avec architecte intégré',
        'features': [
            'Villa individuelle',
            'Immeuble résidentiel',
            'Bâtiment commercial',
            'Construction écologique'
        ],
        'price_range': '500\'000 - 5\'000\'000 CHF'
    },
    'gros-oeuvre': {
        'title': 'Gros Œuvre',
        'meta_title': 'Entreprise Gros Œuvre Genève | Maçonnerie & Structure',
        'meta_description': 'Spécialiste gros œuvre et maçonnerie en Suisse romande. Fondations, dalles, murs porteurs. 30 ans d\'expérience.',
        'slug': 'gros-oeuvre',
        'icon': 'building-4-line',
        'description': 'Expertise en maçonnerie et travaux structurels lourds',
        'features': [
            'Fondations spéciales',
            'Dalles et planchers',
            'Murs porteurs',
            'Travaux de terrassement'
        ],
        'price_range': '100\'000 - 2\'000\'000 CHF'
    }
}

# Projets réalisés
PROJECTS = [
    {
        'id': 1,
        'title': 'Villa Contemporaine - Cologny',
        'category': 'construction-neuve',
        'location': 'Cologny, Genève',
        'year': 2024,
        'budget': '3.2M CHF',
        'duration': '18 mois',
        'surface': '450m²',
        'image': 'villa-cologny.jpg',
        'description': 'Villa d\'exception avec vue lac, piscine infinity et domotique complète',
        'gallery': ['villa-cologny-1.jpg', 'villa-cologny-2.jpg', 'villa-cologny-3.jpg']
    },
    {
        'id': 2,
        'title': 'Rénovation Appartement Haussmannien',
        'category': 'renovation-interieure',
        'location': 'Eaux-Vives, Genève',
        'year': 2024,
        'budget': '850K CHF',
        'duration': '6 mois',
        'surface': '280m²',
        'image': 'appart-eauxvives.jpg',
        'description': 'Rénovation complète avec conservation du cachet historique',
        'gallery': ['appart-1.jpg', 'appart-2.jpg', 'appart-3.jpg']
    },
    {
        'id': 3,
        'title': 'Immeuble Minergie - Lausanne',
        'category': 'isolation-thermique',
        'location': 'Lausanne',
        'year': 2023,
        'budget': '12M CHF',
        'duration': '24 mois',
        'surface': '2800m²',
        'image': 'immeuble-minergie.jpg',
        'description': 'Immeuble résidentiel certifié Minergie-P avec 24 appartements',
        'gallery': ['minergie-1.jpg', 'minergie-2.jpg', 'minergie-3.jpg']
    }
]

# Routes principales
@website.route('/')
def home():
    """Page d'accueil"""
    return render_template('home.html',
        services=SERVICES,
        projects=PROJECTS[:3],
        meta_title='Globibat - Construction & Rénovation Premium Genève | BTP Haut de Gamme',
        meta_description='Entreprise construction et rénovation haut de gamme à Genève. Spécialiste isolation, gros œuvre, rénovation intérieure. Devis gratuit 48h.'
    )

@website.route('/a-propos')
def about():
    """Page À propos"""
    return render_template('about.html',
        meta_title='À Propos - Globibat | 30 Ans d\'Excellence BTP en Suisse',
        meta_description='Découvrez Globibat, leader de la construction premium en Suisse romande depuis 1994. Équipe de 50 experts, 500+ projets réalisés.'
    )

@website.route('/services')
def services_list():
    """Liste des services"""
    return render_template('services.html',
        services=SERVICES,
        meta_title='Nos Services BTP Premium | Rénovation, Construction, Isolation',
        meta_description='Services complets de construction et rénovation: isolation thermique, gros œuvre, construction neuve, rénovation intérieure. Devis gratuit.'
    )

@website.route('/services/<slug>')
def service_detail(slug):
    """Détail d'un service"""
    service = SERVICES.get(slug)
    if not service:
        return redirect(url_for('services_list'))
    
    return render_template('service_detail.html',
        service=service,
        related_projects=[p for p in PROJECTS if p['category'] == slug],
        meta_title=service['meta_title'],
        meta_description=service['meta_description']
    )

@website.route('/projets')
def projects():
    """Portfolio des réalisations"""
    category = request.args.get('category', 'all')
    filtered_projects = PROJECTS if category == 'all' else [p for p in PROJECTS if p['category'] == category]
    
    return render_template('projects.html',
        projects=filtered_projects,
        services=SERVICES,
        current_category=category,
        meta_title='Nos Réalisations | Portfolio Construction & Rénovation Premium',
        meta_description='Découvrez nos projets de construction et rénovation haut de gamme à Genève et en Suisse romande. Villas, appartements, immeubles.'
    )

@website.route('/projets/<int:project_id>')
def project_detail(project_id):
    """Détail d'un projet"""
    project = next((p for p in PROJECTS if p['id'] == project_id), None)
    if not project:
        return redirect(url_for('projects'))
    
    return render_template('project_detail.html',
        project=project,
        related_projects=[p for p in PROJECTS if p['category'] == project['category'] and p['id'] != project_id][:2],
        meta_title=f"{project['title']} | Réalisation Globibat",
        meta_description=f"{project['description']} - Budget: {project['budget']}, Surface: {project['surface']}"
    )

@website.route('/blog')
def blog():
    """Blog avec articles SEO"""
    articles = [
        {
            'slug': 'isolation-thermique-geneve-2026',
            'title': 'Isolation Thermique à Genève : Pourquoi Agir en 2026 ?',
            'excerpt': 'Découvrez les nouvelles normes 2026 et les aides cantonales pour l\'isolation de votre maison à Genève.',
            'date': '15 Janvier 2024',
            'category': 'Isolation',
            'read_time': '5 min'
        },
        {
            'slug': 'renovation-maison-lausanne-guide',
            'title': 'Guide Complet : Rénovation Maison à Lausanne',
            'excerpt': 'Tout ce qu\'il faut savoir pour réussir la rénovation de votre maison à Lausanne en 2024.',
            'date': '10 Janvier 2024',
            'category': 'Rénovation',
            'read_time': '8 min'
        },
        {
            'slug': 'construction-villa-moderne-geneve',
            'title': 'Construire une Villa Moderne à Genève : Prix et Délais',
            'excerpt': 'Analyse complète des coûts et délais pour la construction d\'une villa moderne en 2024.',
            'date': '5 Janvier 2024',
            'category': 'Construction',
            'read_time': '7 min'
        }
    ]
    
    return render_template('blog.html',
        articles=articles,
        meta_title='Blog Construction & Rénovation | Conseils Experts BTP',
        meta_description='Articles et guides sur la construction, rénovation, isolation en Suisse. Conseils d\'experts, normes 2026, aides cantonales.'
    )

@website.route('/blog/<slug>')
def blog_article(slug):
    """Article de blog détaillé"""
    # Ici on pourrait charger depuis une base de données
    articles_content = {
        'isolation-thermique-geneve-2026': {
            'title': 'Isolation Thermique à Genève : Pourquoi Agir en 2026 ?',
            'content': '''
                <h2>Les nouvelles normes énergétiques 2026</h2>
                <p>Le canton de Genève renforce ses exigences en matière d'efficacité énergétique...</p>
                
                <h2>Les aides financières disponibles</h2>
                <table>
                    <tr><th>Type d'aide</th><th>Montant</th><th>Conditions</th></tr>
                    <tr><td>Subvention cantonale</td><td>Jusqu'à 40%</td><td>Minergie</td></tr>
                    <tr><td>Déduction fiscale</td><td>100% déductible</td><td>Propriétaire occupant</td></tr>
                </table>
                
                <h2>Prix moyens isolation Genève 2024</h2>
                <ul>
                    <li>Isolation façade ITE : 180-250 CHF/m²</li>
                    <li>Isolation toiture : 150-200 CHF/m²</li>
                    <li>Isolation sols : 80-120 CHF/m²</li>
                </ul>
            ''',
            'meta_title': 'Isolation Thermique Genève 2026 : Normes, Prix, Aides',
            'meta_description': 'Guide complet isolation thermique Genève 2026. Nouvelles normes, aides cantonales jusqu\'à 40%, prix moyens. Devis gratuit.'
        }
    }
    
    article = articles_content.get(slug)
    if not article:
        return redirect(url_for('blog'))
    
    return render_template('blog_article.html',
        article=article,
        meta_title=article['meta_title'],
        meta_description=article['meta_description']
    )

@website.route('/devis')
@website.route('/devis-renovation-construction-nyon')
def devis():
    """Page de demande de devis"""
    return render_template('devis.html',
        services=SERVICES,
        meta_title='Devis Gratuit Rénovation Construction | Réponse 48h',
        meta_description='Demandez votre devis gratuit pour vos travaux de construction ou rénovation. Réponse détaillée sous 48h. Sans engagement.'
    )

@website.route('/contact')
def contact():
    """Page de contact"""
    return render_template('contact.html',
        meta_title='Contact Globibat Genève | Téléphone, Email, Adresse',
        meta_description='Contactez Globibat pour vos projets de construction et rénovation. Bureau à Genève, intervention Suisse romande. Tél: 022 123 45 67'
    )

# Routes API pour formulaires
@website.route('/api/devis', methods=['POST'])
def submit_devis():
    """Soumission formulaire devis"""
    data = request.json
    # Ici on pourrait sauvegarder en base ou envoyer par email
    # Pour l'instant on simule
    return jsonify({
        'success': True,
        'message': 'Votre demande a été envoyée. Nous vous répondrons sous 48h.',
        'reference': f'DEV-{datetime.now().strftime("%Y%m%d")}-{hash(str(data)) % 1000:03d}'
    })

@website.route('/api/contact', methods=['POST'])
def submit_contact():
    """Soumission formulaire contact"""
    data = request.json
    return jsonify({
        'success': True,
        'message': 'Message envoyé avec succès. Nous vous récontacterons rapidement.'
    })

@website.route('/api/newsletter', methods=['POST'])
def submit_newsletter():
    """Inscription newsletter"""
    email = request.json.get('email')
    return jsonify({
        'success': True,
        'message': 'Inscription confirmée ! Vous recevrez nos actualités mensuelles.'
    })

# Redirections pour le CRM et badge
@website.route('/crm')
def crm_redirect():
    """Redirection vers le CRM"""
    return redirect('http://localhost:5005/login')

@website.route('/badge')
def badge_redirect():
    """Redirection vers le système de badge"""
    return redirect('http://localhost:5005/employee/badge')

# Sitemap pour SEO
@website.route('/sitemap.xml')
def sitemap():
    """Génération du sitemap"""
    pages = []
    
    # Pages statiques
    for rule in website.url_map.iter_rules():
        if "GET" in rule.methods and not rule.rule.startswith('/api'):
            pages.append({
                'loc': url_for(rule.endpoint, _external=True),
                'lastmod': datetime.now().date().isoformat(),
                'changefreq': 'weekly',
                'priority': 0.8
            })
    
    sitemap_xml = render_template('sitemap.xml', pages=pages)
    response = website.make_response(sitemap_xml)
    response.headers["Content-Type"] = "application/xml"
    return response

# Robots.txt
@website.route('/robots.txt')
def robots():
    return website.send_static_file('robots.txt')

# Favicon
@website.route('/favicon.ico')
def favicon():
    return website.send_static_file('favicon.ico')

if __name__ == '__main__':
    # Créer les dossiers nécessaires
    os.makedirs('website/templates', exist_ok=True)
    os.makedirs('website/static/css', exist_ok=True)
    os.makedirs('website/static/js', exist_ok=True)
    os.makedirs('website/static/images', exist_ok=True)
    os.makedirs('website/static/fonts', exist_ok=True)
    
    print("\n" + "="*50)
    print("🌐 SITE WEB GLOBIBAT")
    print("="*50)
    print("\n📍 URLs d'accès:")
    print("   Site Web: http://localhost:5000")
    print("   CRM: http://localhost:5000/crm → :5005/login")
    print("   Badge: http://localhost:5000/badge → :5005/employee/badge")
    print("="*50 + "\n")
    
    website.run(debug=True, port=5000, host='0.0.0.0')
