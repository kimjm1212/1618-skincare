// Navbar shadow on scroll
const navbar = document.querySelector('.navbar');
const onScroll = () => navbar.classList.toggle('scrolled', window.scrollY > 10);
window.addEventListener('scroll', onScroll, { passive: true });
onScroll();

// Mobile menu
const hamburger = document.querySelector('.hamburger');
const navMenu = document.querySelector('.nav-menu');
if (hamburger && navMenu) {
    hamburger.addEventListener('click', () => navMenu.classList.toggle('active'));
    navMenu.addEventListener('click', (e) => {
        if (e.target.tagName === 'A') navMenu.classList.remove('active');
    });
}

// Reveal sections on scroll
const targets = document.querySelectorAll('.ratio-item, .product-card, .split-text, .formula-text');
if (targets.length) {
    const io = new IntersectionObserver((entries) => {
        entries.forEach((e) => {
            if (e.isIntersecting) { e.target.classList.add('in'); io.unobserve(e.target); }
        });
    }, { rootMargin: '0px 0px -60px 0px' });
    targets.forEach((el) => { el.classList.add('reveal'); io.observe(el); });
}

// Highlight the nav link of the section in view (in-page anchors only)
const anchors = [...document.querySelectorAll('.nav-menu a[href^="#"]')];
const sections = anchors
    .map((a) => document.querySelector(a.getAttribute('href')))
    .filter(Boolean);

if (sections.length) {
    const spy = new IntersectionObserver((entries) => {
        entries.forEach((e) => {
            if (!e.isIntersecting) return;
            anchors.forEach((a) => a.classList.toggle('active', a.getAttribute('href') === '#' + e.target.id));
        });
    }, { rootMargin: '-45% 0px -50% 0px' });
    sections.forEach((s) => spy.observe(s));
}
