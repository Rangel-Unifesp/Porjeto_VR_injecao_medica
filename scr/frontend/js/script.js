// Script principal para o site do projeto VR

document.addEventListener('DOMContentLoaded', function() {
    // Menu mobile toggle
    const menuToggle = document.querySelector('.menu-toggle');
    const navMenu = document.querySelector('.nav-menu');
    
    if (menuToggle) {
        menuToggle.addEventListener('click', function() {
            navMenu.classList.toggle('active');
        });
    }
    
    // Fechar menu ao clicar em um link
    const navLinks = document.querySelectorAll('.nav-menu a');
    navLinks.forEach(link => {
        link.addEventListener('click', function() {
            navMenu.classList.remove('active');
        });
    });
    
    // Destacar link ativo durante a rolagem
    window.addEventListener('scroll', function() {
        const sections = document.querySelectorAll('section');
        const navLinks = document.querySelectorAll('.nav-menu a');
        
        let current = '';
        
        sections.forEach(section => {
            const sectionTop = section.offsetTop;
            const sectionHeight = section.clientHeight;
            
            if (pageYOffset >= (sectionTop - 200)) {
                current = section.getAttribute('id');
            }
        });
        
        navLinks.forEach(link => {
            link.classList.remove('active');
            if (link.getAttribute('href') === `#${current}`) {
                link.classList.add('active');
            }
        });
    });
    
    // Formulário de contato
    const contactForm = document.getElementById('contactForm');
    if (contactForm) {
        contactForm.addEventListener('submit', function(e) {
            e.preventDefault();
            
            // Simulação de envio de formulário
            const name = document.getElementById('name').value;
            const email = document.getElementById('email').value;
            const message = document.getElementById('message').value;
            
            // Validação básica
            if (name && email && message) {
                // Aqui seria a lógica de envio real
                alert('Obrigado pela sua mensagem! Em um ambiente de produção, sua mensagem seria enviada.');
                contactForm.reset();
            } else {
                alert('Por favor, preencha todos os campos.');
            }
        });
    }
    
    // Animação de fade-in para elementos ao rolar
    const fadeElements = document.querySelectorAll('.tech-card, .component-card, .timeline-item');
    
    const fadeInOptions = {
        threshold: 0.3,
        rootMargin: "0px 0px -100px 0px"
    };
    
    const fadeInObserver = new IntersectionObserver(function(entries, observer) {
        entries.forEach(entry => {
            if (!entry.isIntersecting) {
                return;
            }
            entry.target.classList.add('fade-in');
            observer.unobserve(entry.target);
        });
    }, fadeInOptions);
    
    fadeElements.forEach(element => {
        element.style.opacity = "0";
        element.style.transition = "opacity 0.5s ease-in-out, transform 0.5s ease-in-out";
        element.style.transform = "translateY(20px)";
        fadeInObserver.observe(element);
    });
    
    // Classe para elementos que aparecem na tela
    document.querySelectorAll('.fade-in').forEach(el => {
        el.style.opacity = "1";
        el.style.transform = "translateY(0)";
    });
});
