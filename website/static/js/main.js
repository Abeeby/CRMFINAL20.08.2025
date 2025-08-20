/**
 * GLOBIBAT - Main JavaScript
 * Animations GSAP, interactions et fonctionnalités premium
 */

// Attendre le chargement du DOM
document.addEventListener('DOMContentLoaded', function() {
    
    // Preloader
    const preloader = document.getElementById('preloader');
    window.addEventListener('load', () => {
        setTimeout(() => {
            preloader.style.opacity = '0';
            setTimeout(() => {
                preloader.style.display = 'none';
            }, 500);
        }, 500);
    });
    
    // Custom Cursor (desktop only)
    if (window.innerWidth > 1024) {
        const cursor = document.querySelector('.cursor');
        const cursorFollower = document.querySelector('.cursor-follower');
        
        document.addEventListener('mousemove', (e) => {
            cursor.style.left = e.clientX + 'px';
            cursor.style.top = e.clientY + 'px';
            
            setTimeout(() => {
                cursorFollower.style.left = e.clientX - 10 + 'px';
                cursorFollower.style.top = e.clientY - 10 + 'px';
            }, 100);
        });
        
        // Hover effects
        const links = document.querySelectorAll('a, button');
        links.forEach(link => {
            link.addEventListener('mouseenter', () => {
                cursor.style.transform = 'scale(1.5)';
                cursorFollower.style.transform = 'scale(1.5)';
            });
            link.addEventListener('mouseleave', () => {
                cursor.style.transform = 'scale(1)';
                cursorFollower.style.transform = 'scale(1)';
            });
        });
    }
    
    // Mobile Menu Toggle
    const navToggle = document.getElementById('navToggle');
    const navMenu = document.getElementById('navMenu');
    
    if (navToggle) {
        navToggle.addEventListener('click', () => {
            navMenu.classList.toggle('active');
            navToggle.classList.toggle('active');
            
            // Animate burger menu
            const spans = navToggle.querySelectorAll('span');
            if (navToggle.classList.contains('active')) {
                spans[0].style.transform = 'rotate(45deg) translateY(8px)';
                spans[1].style.opacity = '0';
                spans[2].style.transform = 'rotate(-45deg) translateY(-8px)';
            } else {
                spans[0].style.transform = 'none';
                spans[1].style.opacity = '1';
                spans[2].style.transform = 'none';
            }
        });
    }
    
    // Header Scroll Effect
    const header = document.getElementById('header');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            header.classList.add('scrolled');
            header.style.boxShadow = '0 4px 20px rgba(0,0,0,0.1)';
        } else {
            header.classList.remove('scrolled');
            header.style.boxShadow = 'none';
        }
        
        // Hide/Show on scroll
        if (currentScroll > lastScroll && currentScroll > 500) {
            header.style.transform = 'translateY(-100%)';
        } else {
            header.style.transform = 'translateY(0)';
        }
        
        lastScroll = currentScroll;
    });
    
    // GSAP Animations
    gsap.registerPlugin(ScrollTrigger, TextPlugin);
    
    // Hero animations
    const heroTimeline = gsap.timeline();
    
    heroTimeline
        .from('.hero-subtitle', {
            opacity: 0,
            y: 30,
            duration: 1,
            ease: 'power3.out'
        })
        .from('.hero-title .hero-line', {
            opacity: 0,
            y: 50,
            duration: 1,
            stagger: 0.2,
            ease: 'power3.out'
        }, '-=0.5')
        .from('.hero-description', {
            opacity: 0,
            y: 30,
            duration: 1,
            ease: 'power3.out'
        }, '-=0.5')
        .from('.hero-buttons .btn', {
            opacity: 0,
            y: 30,
            duration: 1,
            stagger: 0.2,
            ease: 'power3.out'
        }, '-=0.5')
        .from('.stat-item', {
            opacity: 0,
            y: 30,
            duration: 1,
            stagger: 0.1,
            ease: 'power3.out'
        }, '-=0.5');
    
    // Scroll animations
    gsap.utils.toArray('.section-header').forEach(header => {
        gsap.from(header, {
            opacity: 0,
            y: 50,
            duration: 1,
            scrollTrigger: {
                trigger: header,
                start: 'top 80%',
                once: true
            }
        });
    });
    
    gsap.utils.toArray('.service-card').forEach((card, index) => {
        gsap.from(card, {
            opacity: 0,
            y: 50,
            duration: 1,
            delay: index * 0.1,
            scrollTrigger: {
                trigger: card,
                start: 'top 80%',
                once: true
            }
        });
    });
    
    // Process timeline animation
    gsap.utils.toArray('.process-step').forEach((step, index) => {
        gsap.from(step, {
            opacity: 0,
            x: index % 2 === 0 ? -50 : 50,
            duration: 1,
            scrollTrigger: {
                trigger: step,
                start: 'top 80%',
                once: true
            }
        });
    });
    
    // Parallax effect
    gsap.utils.toArray('.parallax').forEach(element => {
        gsap.to(element, {
            yPercent: -50,
            ease: 'none',
            scrollTrigger: {
                trigger: element,
                start: 'top bottom',
                end: 'bottom top',
                scrub: true
            }
        });
    });
    
    // Back to top button
    const backToTop = document.getElementById('backToTop');
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > 500) {
            backToTop.style.opacity = '1';
            backToTop.style.visibility = 'visible';
        } else {
            backToTop.style.opacity = '0';
            backToTop.style.visibility = 'hidden';
        }
    });
    
    if (backToTop) {
        backToTop.addEventListener('click', () => {
            window.scrollTo({
                top: 0,
                behavior: 'smooth'
            });
        });
    }
    
    // Exit Intent Popup
    let exitIntentShown = false;
    const exitPopup = document.getElementById('exitPopup');
    const popupClose = document.getElementById('popupClose');
    
    document.addEventListener('mouseout', (e) => {
        if (!exitIntentShown && e.clientY <= 0 && exitPopup) {
            exitPopup.style.display = 'flex';
            exitIntentShown = true;
            
            // Track event
            if (typeof gtag !== 'undefined') {
                gtag('event', 'exit_intent_shown', {
                    'event_category': 'engagement'
                });
            }
        }
    });
    
    if (popupClose) {
        popupClose.addEventListener('click', () => {
            exitPopup.style.display = 'none';
        });
    }
    
    // Form submissions
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            // Get form action
            const action = form.getAttribute('action') || '/api/contact';
            
            try {
                const response = await fetch(action, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Show success message
                    showNotification('Succès', result.message, 'success');
                    form.reset();
                    
                    // Track conversion
                    if (typeof gtag !== 'undefined') {
                        gtag('event', 'form_submission', {
                            'event_category': 'engagement',
                            'event_label': form.id || 'form'
                        });
                    }
                } else {
                    showNotification('Erreur', 'Une erreur est survenue', 'error');
                }
            } catch (error) {
                showNotification('Erreur', 'Impossible d\'envoyer le formulaire', 'error');
            }
        });
    });
    
    // Notification system
    function showNotification(title, message, type = 'info') {
        const notification = document.createElement('div');
        notification.className = `notification notification-${type}`;
        notification.innerHTML = `
            <div class="notification-content">
                <h4>${title}</h4>
                <p>${message}</p>
            </div>
        `;
        
        document.body.appendChild(notification);
        
        // Animate in
        gsap.from(notification, {
            x: 300,
            opacity: 0,
            duration: 0.5,
            ease: 'power3.out'
        });
        
        // Remove after 5 seconds
        setTimeout(() => {
            gsap.to(notification, {
                x: 300,
                opacity: 0,
                duration: 0.5,
                ease: 'power3.in',
                onComplete: () => notification.remove()
            });
        }, 5000);
    }
    
    // Smooth scroll for anchor links
    document.querySelectorAll('a[href^="#"]').forEach(anchor => {
        anchor.addEventListener('click', function(e) {
            e.preventDefault();
            const target = document.querySelector(this.getAttribute('href'));
            if (target) {
                target.scrollIntoView({
                    behavior: 'smooth',
                    block: 'start'
                });
            }
        });
    });
    
    // Lazy loading images
    const lazyImages = document.querySelectorAll('img[loading="lazy"]');
    
    if ('IntersectionObserver' in window) {
        const imageObserver = new IntersectionObserver((entries, observer) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const img = entry.target;
                    img.src = img.dataset.src || img.src;
                    img.classList.add('loaded');
                    observer.unobserve(img);
                }
            });
        });
        
        lazyImages.forEach(img => imageObserver.observe(img));
    }
    
    // AOS-like animations
    const animateElements = document.querySelectorAll('[data-aos]');
    
    if (animateElements.length > 0) {
        const animateObserver = new IntersectionObserver((entries) => {
            entries.forEach(entry => {
                if (entry.isIntersecting) {
                    const element = entry.target;
                    const animation = element.dataset.aos;
                    const delay = element.dataset.aosDelay || 0;
                    
                    setTimeout(() => {
                        element.classList.add('aos-animate');
                    }, delay);
                    
                    animateObserver.unobserve(element);
                }
            });
        }, {
            threshold: 0.1
        });
        
        animateElements.forEach(el => animateObserver.observe(el));
    }
});

// Add CSS for notifications
const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        top: 100px;
        right: 20px;
        background: white;
        padding: 20px;
        border-radius: 10px;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        z-index: 9999;
        max-width: 350px;
    }
    
    .notification-success {
        border-left: 4px solid #10b981;
    }
    
    .notification-error {
        border-left: 4px solid #ef4444;
    }
    
    .notification-info {
        border-left: 4px solid #3b82f6;
    }
    
    .notification h4 {
        margin: 0 0 5px 0;
        font-size: 16px;
        font-weight: 600;
    }
    
    .notification p {
        margin: 0;
        font-size: 14px;
        color: #6b7280;
    }
    
    [data-aos] {
        opacity: 0;
        transition: opacity 0.6s, transform 0.6s;
    }
    
    [data-aos="fade-up"] {
        transform: translateY(30px);
    }
    
    [data-aos="fade-down"] {
        transform: translateY(-30px);
    }
    
    [data-aos="fade-left"] {
        transform: translateX(30px);
    }
    
    [data-aos="fade-right"] {
        transform: translateX(-30px);
    }
    
    [data-aos].aos-animate {
        opacity: 1;
        transform: translateX(0) translateY(0);
    }
`;
document.head.appendChild(style);
