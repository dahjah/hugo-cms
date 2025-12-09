document.addEventListener('DOMContentLoaded', function() {
    // --- Carousel Logic ---
    const carousels = document.querySelectorAll('.carousel-block');
    
    carousels.forEach(carousel => {
        const track = carousel.querySelector('.carousel-track');
        const slides = Array.from(track.children);
        const nextButton = carousel.querySelector('.carousel-next');
        const prevButton = carousel.querySelector('.carousel-prev');
        const dotsNav = carousel.querySelector('.carousel-dots');
        const dots = dotsNav ? Array.from(dotsNav.children) : [];
        
        if (slides.length === 0) return;
        
        const slideWidth = slides[0].getBoundingClientRect().width;
        
        // Arrange slides next to one another
        slides.forEach((slide, index) => {
            slide.style.left = slideWidth * index + 'px';
        });
        
        const moveToSlide = (track, currentSlide, targetSlide) => {
            track.style.transform = 'translateX(-' + targetSlide.style.left + ')';
            currentSlide.classList.remove('current-slide');
            targetSlide.classList.add('current-slide');
        };
        
        const updateDots = (currentDot, targetDot) => {
            if (!currentDot || !targetDot) return;
            currentDot.classList.remove('active');
            targetDot.classList.add('active');
        };
        
        // Next button
        if (nextButton) {
            nextButton.addEventListener('click', e => {
                const currentSlide = track.querySelector('.current-slide') || slides[0];
                const nextSlide = currentSlide.nextElementSibling || slides[0];
                const currentDot = dotsNav.querySelector('.active') || dots[0];
                const nextDot = currentDot.nextElementSibling || dots[0];
                
                moveToSlide(track, currentSlide, nextSlide);
                updateDots(currentDot, nextDot);
            });
        }
        
        // Prev button
        if (prevButton) {
            prevButton.addEventListener('click', e => {
                const currentSlide = track.querySelector('.current-slide') || slides[0];
                const prevSlide = currentSlide.previousElementSibling || slides[slides.length - 1];
                const currentDot = dotsNav.querySelector('.active') || dots[0];
                const prevDot = currentDot.previousElementSibling || dots[dots.length - 1];
                
                moveToSlide(track, currentSlide, prevSlide);
                updateDots(currentDot, prevDot);
            });
        }
        
        // Dots
        if (dotsNav) {
            dotsNav.addEventListener('click', e => {
                const targetDot = e.target.closest('button');
                if (!targetDot) return;
                
                const currentSlide = track.querySelector('.current-slide') || slides[0];
                const currentDot = dotsNav.querySelector('.active') || dots[0];
                const targetIndex = dots.findIndex(dot => dot === targetDot);
                const targetSlide = slides[targetIndex];
                
                moveToSlide(track, currentSlide, targetSlide);
                updateDots(currentDot, targetDot);
            });
        }
        
        // Auto advance
        setInterval(() => {
            if (nextButton) nextButton.click();
        }, 8000);
    });
    
    // --- Accordion Logic ---
    const accordions = document.querySelectorAll('.accordion-item');
    
    accordions.forEach(item => {
        const header = item.querySelector('.accordion-header');
        
        header.addEventListener('click', () => {
            const isOpen = item.hasAttribute('open');
            
            // Close others if needed (optional)
            // accordions.forEach(i => i.removeAttribute('open'));
            
            if (isOpen) {
                item.removeAttribute('open');
            } else {
                item.setAttribute('open', '');
            }
        });
    });
});
