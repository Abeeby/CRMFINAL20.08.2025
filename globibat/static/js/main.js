/**
 * GLOBIBAT - Main JavaScript
 * Animations GSAP premium et micro-interactions
 */

// Configuration GSAP
gsap.registerPlugin(ScrollTrigger, TextPlugin);

// Variables globales
let lenis;
let cursor;
let cursorFollower;

// Initialisation
document.addEventListener('DOMContentLoaded', function() {
    initPreloader();
    initSmoothScroll();
    initCustomCursor();
    initHeader();
    initAnimations();
    initHeroAnimations();
    initCounters();
    initBeforeAfterSlider();
    initTimelineProgress();
    initTestimonialsCarousel();
    initPartnersCarousel();
    initFAQAccordions();
    initStickyCTA();
    initBackToTop();
    initMobileMenu();
    initFormValidation();
});

/**
 * Preloader
 */
function initPreloader() {
    const preloader = document.getElementById('preloader');
    
    window.addEventListener('load', () => {
        setTimeout(() => {
            preloader.classList.add('loaded');
            
            // Animation d'entrée après le preloader
            gsap.timeline()
                .from('.hero-badges', {
                    y: 30,
                    opacity: 0,
                    duration: 0.8,
                    ease: 'power3.out'
                })
                .from('.hero-title .line', {
                    y: 100,
                    opacity: 0,
                    duration: 1,
                    stagger: 0.1,
                    ease: 'power3.out'
                }, '-=0.4')
                .from('.hero-subtitle', {
                    y: 30,
                    opacity: 0,
                    duration: 0.8,
                    ease: 'power3.out'
                }, '-=0.4')
                .from('.hero-cta > *', {
                    y: 30,
                    opacity: 0,
                    duration: 0.8,
                    stagger: 0.1,
                    ease: 'power3.out'
                }, '-=0.4')
                .from('.hero-scroll', {
                    y: 30,
                    opacity: 0,
                    duration: 0.8,
                    ease: 'power3.out'
                }, '-=0.4');
        }, 500);
    });
}

/**
 * Smooth Scroll avec Lenis
 */
function initSmoothScroll() {
    // Check if mobile
    if (window.innerWidth <= 768) {
        return;
    }
    
    lenis = new Lenis({
        duration: 1.2,
        easing: (t) => Math.min(1, 1.001 - Math.pow(2, -10 * t)),
        direction: 'vertical',
        gestureDirection: 'vertical',
        smooth: true,
        mouseMultiplier: 1,
        smoothTouch: false,
        touchMultiplier: 2,
        infinite: false,
    });
    
    function raf(time) {
        lenis.raf(time);
        requestAnimationFrame(raf);
    }
    
    requestAnimationFrame(raf);
    
    // Synchronisation avec ScrollTrigger
    lenis.on('scroll', ScrollTrigger.update);
    
    gsap.ticker.add((time) => {
        lenis.raf(time * 1000);
    });
    
    gsap.ticker.lagSmoothing(0);
}

/**
 * Custom Cursor
 */
function initCustomCursor() {
    // Check if touch device
    if ('ontouchstart' in window) {
        return;
    }
    
    cursor = document.getElementById('cursor');
    cursorFollower = document.getElementById('cursor-follower');
    
    if (!cursor || !cursorFollower) return;
    
    let mouseX = 0;
    let mouseY = 0;
    let cursorX = 0;
    let cursorY = 0;
    let followerX = 0;
    let followerY = 0;
    
    document.addEventListener('mousemove', (e) => {
        mouseX = e.clientX;
        mouseY = e.clientY;
    });
    
    // Animation du curseur
    gsap.ticker.add(() => {
        cursorX += (mouseX - cursorX) * 0.5;
        cursorY += (mouseY - cursorY) * 0.5;
        followerX += (mouseX - followerX) * 0.1;
        followerY += (mouseY - followerY) * 0.1;
        
        gsap.set(cursor, {
            x: cursorX,
            y: cursorY
        });
        
        gsap.set(cursorFollower, {
            x: followerX,
            y: followerY
        });
    });
    
    // Hover effects
    document.querySelectorAll('[data-cursor="hover"]').forEach(el => {
        el.addEventListener('mouseenter', () => {
            cursor.classList.add('hover');
            cursorFollower.classList.add('hover');
        });
        
        el.addEventListener('mouseleave', () => {
            cursor.classList.remove('hover');
            cursorFollower.classList.remove('hover');
        });
    });
}

/**
 * Header scroll effects
 */
function initHeader() {
    const header = document.getElementById('header');
    let lastScroll = 0;
    
    window.addEventListener('scroll', () => {
        const currentScroll = window.pageYOffset;
        
        if (currentScroll > 100) {
            header.classList.add('scrolled');
        } else {
            header.classList.remove('scrolled');
        }
        
        lastScroll = currentScroll;
    });
}

/**
 * Animations générales
 */
function initAnimations() {
    // Fade up animations
    gsap.utils.toArray('[data-animation="fade-up"]').forEach(element => {
        gsap.fromTo(element, 
            {
                y: 30,
                opacity: 0
            },
            {
                y: 0,
                opacity: 1,
                duration: 0.8,
                ease: 'power3.out',
                scrollTrigger: {
                    trigger: element,
                    start: 'top 85%',
                    once: true
                }
            }
        );
    });
    
    // Stagger animations
    gsap.utils.toArray('[data-animation="stagger"]').forEach(container => {
        const elements = container.children;
        
        gsap.fromTo(elements,
            {
                y: 30,
                opacity: 0
            },
            {
                y: 0,
                opacity: 1,
                duration: 0.8,
                stagger: 0.1,
                ease: 'power3.out',
                scrollTrigger: {
                    trigger: container,
                    start: 'top 85%',
                    once: true
                }
            }
        );
    });
}

/**
 * Hero Animations
 */
function initHeroAnimations() {
    // Parallax effect on scroll
    gsap.to('.hero-bg', {
        yPercent: 50,
        ease: 'none',
        scrollTrigger: {
            trigger: '.hero',
            start: 'top top',
            end: 'bottom top',
            scrub: true
        }
    });
}

/**
 * Counters Animation
 */
function initCounters() {
    const counters = document.querySelectorAll('[data-animation="counter"] .proof-number');
    
    counters.forEach(counter => {
        const target = parseInt(counter.getAttribute('data-count'));
        
        gsap.fromTo(counter,
            {
                textContent: 0
            },
            {
                textContent: target,
                duration: 2,
                ease: 'power2.out',
                snap: { textContent: 1 },
                scrollTrigger: {
                    trigger: counter,
                    start: 'top 85%',
                    once: true
                }
            }
        );
    });
}

/**
 * Before/After Slider
 */
function initBeforeAfterSlider() {
    const slider = document.getElementById('beforeAfterSlider');
    if (!slider) return;
    
    const handle = document.getElementById('baHandle');
    const afterImage = slider.querySelector('.after-image');
    
    let isDragging = false;
    
    const updateSlider = (x) => {
        const rect = slider.getBoundingClientRect();
        let position = ((x - rect.left) / rect.width) * 100;
        position = Math.max(0, Math.min(100, position));
        
        handle.style.left = position + '%';
        afterImage.style.clipPath = `inset(0 0 0 ${position}%)`;
    };
    
    // Mouse events
    handle.addEventListener('mousedown', () => isDragging = true);
    
    document.addEventListener('mousemove', (e) => {
        if (isDragging) {
            updateSlider(e.clientX);
        }
    });
    
    document.addEventListener('mouseup', () => isDragging = false);
    
    // Touch events
    handle.addEventListener('touchstart', () => isDragging = true);
    
    document.addEventListener('touchmove', (e) => {
        if (isDragging) {
            updateSlider(e.touches[0].clientX);
        }
    });
    
    document.addEventListener('touchend', () => isDragging = false);
    
    // Click to position
    slider.addEventListener('click', (e) => {
        if (e.target !== handle && !handle.contains(e.target)) {
            updateSlider(e.clientX);
        }
    });
}

/**
 * Timeline Progress
 */
function initTimelineProgress() {
    const timeline = document.getElementById('processTimeline');
    if (!timeline) return;
    
    const progressBar = document.getElementById('timelineProgress');
    const steps = timeline.querySelectorAll('.timeline-step');
    
    ScrollTrigger.create({
        trigger: timeline,
        start: 'top center',
        end: 'bottom center',
        scrub: true,
        onUpdate: (self) => {
            const progress = self.progress * 100;
            progressBar.style.height = progress + '%';
            
            // Activer les étapes
            steps.forEach((step, index) => {
                const stepProgress = (index + 1) / steps.length;
                if (self.progress >= stepProgress) {
                    step.classList.add('active');
                } else {
                    step.classList.remove('active');
                }
            });
        }
    });
}

/**
 * Testimonials Carousel
 */
function initTestimonialsCarousel() {
    const carousel = document.getElementById('testimonialsCarousel');
    if (!carousel) return;
    
    new Swiper(carousel, {
        slidesPerView: 1,
        spaceBetween: 30,
        loop: true,
        autoplay: {
            delay: 5000,
            disableOnInteraction: false,
        },
        pagination: {
            el: '.swiper-pagination',
            clickable: true,
        },
        breakpoints: {
            768: {
                slidesPerView: 2,
            },
            1024: {
                slidesPerView: 3,
            }
        }
    });
}

/**
 * Partners Carousel
 */
function initPartnersCarousel() {
    const carousel = document.getElementById('partnersCarousel');
    if (!carousel) return;
    
    new Swiper(carousel, {
        slidesPerView: 2,
        spaceBetween: 30,
        loop: true,
        autoplay: {
            delay: 3000,
            disableOnInteraction: false,
        },
        breakpoints: {
            640: {
                slidesPerView: 3,
            },
            768: {
                slidesPerView: 4,
            },
            1024: {
                slidesPerView: 5,
            }
        }
    });
}

/**
 * FAQ Accordions
 */
function initFAQAccordions() {
    const questions = document.querySelectorAll('.faq-question');
    
    questions.forEach(question => {
        question.addEventListener('click', () => {
            const item = question.parentElement;
            const isActive = item.classList.contains('active');
            
            // Fermer tous les autres
            document.querySelectorAll('.faq-item').forEach(faq => {
                faq.classList.remove('active');
            });
            
            // Toggle current
            if (!isActive) {
                item.classList.add('active');
            }
        });
    });
}

/**
 * Sticky CTA
 */
function initStickyCTA() {
    const stickyCTA = document.getElementById('stickyCTA');
    if (!stickyCTA) return;
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > window.innerHeight * 0.4) {
            stickyCTA.classList.add('visible');
        } else {
            stickyCTA.classList.remove('visible');
        }
    });
}

/**
 * Back to Top
 */
function initBackToTop() {
    const backToTop = document.getElementById('backToTop');
    if (!backToTop) return;
    
    window.addEventListener('scroll', () => {
        if (window.pageYOffset > window.innerHeight) {
            backToTop.classList.add('visible');
        } else {
            backToTop.classList.remove('visible');
        }
    });
    
    backToTop.addEventListener('click', () => {
        if (lenis) {
            lenis.scrollTo(0, { duration: 1.5 });
        } else {
            window.scrollTo({ top: 0, behavior: 'smooth' });
        }
    });
}

/**
 * Mobile Menu
 */
function initMobileMenu() {
    const toggle = document.getElementById('navToggle');
    const menu = document.getElementById('navMenu');
    
    if (!toggle || !menu) return;
    
    toggle.addEventListener('click', () => {
        toggle.classList.toggle('active');
        menu.classList.toggle('active');
        document.body.classList.toggle('menu-open');
    });
    
    // Fermer le menu au clic sur un lien
    document.querySelectorAll('.nav-link').forEach(link => {
        link.addEventListener('click', () => {
            toggle.classList.remove('active');
            menu.classList.remove('active');
            document.body.classList.remove('menu-open');
        });
    });
}

/**
 * Form Validation
 */
function initFormValidation() {
    const forms = document.querySelectorAll('form');
    
    forms.forEach(form => {
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            
            const formData = new FormData(form);
            const data = Object.fromEntries(formData);
            
            // Animation du bouton
            const submitBtn = form.querySelector('[type="submit"]');
            const originalText = submitBtn.innerHTML;
            submitBtn.innerHTML = '<i class="ri-loader-4-line"></i> Envoi en cours...';
            submitBtn.disabled = true;
            
            try {
                const response = await fetch(form.action, {
                    method: form.method,
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(data)
                });
                
                const result = await response.json();
                
                if (result.success) {
                    // Success animation
                    submitBtn.innerHTML = '<i class="ri-check-line"></i> Envoyé !';
                    submitBtn.classList.add('success');
                    
                    // Reset form
                    setTimeout(() => {
                        form.reset();
                        submitBtn.innerHTML = originalText;
                        submitBtn.disabled = false;
                        submitBtn.classList.remove('success');
                    }, 3000);
                    
                    // Show success message
                    showNotification('Votre message a été envoyé avec succès !', 'success');
                } else {
                    throw new Error(result.error || 'Une erreur est survenue');
                }
            } catch (error) {
                submitBtn.innerHTML = originalText;
                submitBtn.disabled = false;
                showNotification(error.message, 'error');
            }
        });
    });
}

/**
 * Show Notification
 */
function showNotification(message, type = 'info') {
    const notification = document.createElement('div');
    notification.className = `notification notification-${type}`;
    notification.innerHTML = `
        <i class="ri-${type === 'success' ? 'check' : 'error'}-line"></i>
        <span>${message}</span>
    `;
    
    document.body.appendChild(notification);
    
    // Animation
    gsap.fromTo(notification,
        {
            y: -100,
            opacity: 0
        },
        {
            y: 20,
            opacity: 1,
            duration: 0.5,
            ease: 'power3.out'
        }
    );
    
    // Remove after 5 seconds
    setTimeout(() => {
        gsap.to(notification, {
            y: -100,
            opacity: 0,
            duration: 0.5,
            ease: 'power3.in',
            onComplete: () => notification.remove()
        });
    }, 5000);
}

// Notification styles
const style = document.createElement('style');
style.textContent = `
    .notification {
        position: fixed;
        top: 0;
        left: 50%;
        transform: translateX(-50%);
        background: var(--color-dark);
        color: var(--color-white);
        padding: 1rem 2rem;
        border-radius: var(--radius-lg);
        box-shadow: var(--shadow-xl);
        z-index: 9999;
        display: flex;
        align-items: center;
        gap: 0.75rem;
        min-width: 300px;
    }
    
    .notification-success {
        background: var(--color-success);
    }
    
    .notification-error {
        background: var(--color-danger);
    }
    
    body.menu-open {
        overflow: hidden;
    }
`;
document.head.appendChild(style);
