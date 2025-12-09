// Testimonials Carousel
document.addEventListener('DOMContentLoaded', function () {
    const carousel = document.querySelector('.testimonials');
    if (!carousel) {
        return;
    }

    const testimonials = Array.from(carousel.querySelectorAll('.testimonial'));

    if (testimonials.length <= 1) {
        return;
    }

    // Lazy load carousel interaction
    const initCarousel = () => {
        let currentIndex = 0;
        let isTransitioning = false;

        // Create carousel wrapper
        carousel.classList.add('testimonials-carousel');

        // Create navigation dots
        const dotsContainer = document.createElement('div');
        dotsContainer.className = 'carousel-dots';
        testimonials.forEach((_, index) => {
            const dot = document.createElement('button');
            dot.className = 'carousel-dot';
            dot.setAttribute('aria-label', `Go to testimonial ${index + 1}`);
            if (index === 0) dot.classList.add('active');
            dot.addEventListener('click', () => {
                const direction = index > currentIndex ? 'next' : 'prev';
                goToSlide(index, direction);
            });
            dotsContainer.appendChild(dot);
        });

        // Create prev/next buttons
        const prevBtn = document.createElement('button');
        prevBtn.className = 'carousel-btn carousel-prev';
        prevBtn.innerHTML = '‹';
        prevBtn.setAttribute('aria-label', 'Previous testimonial');
        prevBtn.addEventListener('click', prevSlide);

        const nextBtn = document.createElement('button');
        nextBtn.className = 'carousel-btn carousel-next';
        nextBtn.innerHTML = '›';
        nextBtn.setAttribute('aria-label', 'Next testimonial');
        nextBtn.addEventListener('click', nextSlide);

        // Add controls to DOM
        carousel.appendChild(prevBtn);
        carousel.appendChild(nextBtn);
        carousel.parentElement.appendChild(dotsContainer);

        // Initialize - set first as active, position others off-screen
        testimonials.forEach((testimonial, index) => {
            if (index === 0) {
                testimonial.classList.add('active');
            } else {
                testimonial.classList.add('slide-in-from-right');
            }
        });

        function goToSlide(index, direction = 'next') {
            if (index === currentIndex || isTransitioning) return;

            isTransitioning = true;
            const currentSlide = testimonials[currentIndex];
            const nextSlide = testimonials[index];

            // Update dots
            const dots = document.querySelectorAll('.carousel-dot');
            if (dots.length > currentIndex) dots[currentIndex].classList.remove('active');
            if (dots.length > index) dots[index].classList.add('active');

            if (direction === 'next') {
                // Current slides out to left
                currentSlide.classList.remove('active');
                currentSlide.classList.add('slide-out-to-left');

                // New slides in from right
                nextSlide.classList.remove('slide-in-from-right', 'slide-in-from-left');
                nextSlide.classList.add('slide-in-from-right');

                // Force reflow
                void nextSlide.offsetWidth;

                nextSlide.classList.remove('slide-in-from-right');
                nextSlide.classList.add('active');
            } else {
                // Current slides out to right
                currentSlide.classList.remove('active');
                currentSlide.classList.add('slide-out-to-right');

                // New slides in from left
                nextSlide.classList.remove('slide-in-from-right', 'slide-in-from-left');
                nextSlide.classList.add('slide-in-from-left');

                // Force reflow
                void nextSlide.offsetWidth;

                nextSlide.classList.remove('slide-in-from-left');
                nextSlide.classList.add('active');
            }

            currentIndex = index;

            // Reset after transition
            setTimeout(() => {
                // Clean up old slide classes
                testimonials.forEach(t => {
                    if (t !== testimonials[currentIndex]) {
                        t.classList.remove('active', 'slide-out-to-left', 'slide-out-to-right');
                        // Position off-screen for next time
                        t.classList.add(direction === 'next' ? 'slide-in-from-right' : 'slide-in-from-left');
                    }
                });
                isTransitioning = false;
            }, 500);
        }

        function nextSlide() {
            const nextIndex = (currentIndex + 1) % testimonials.length;
            goToSlide(nextIndex, 'next');
        }

        function prevSlide() {
            const prevIndex = (currentIndex - 1 + testimonials.length) % testimonials.length;
            goToSlide(prevIndex, 'prev');
        }

        // Auto-advance every 8 seconds
        setInterval(nextSlide, 8000);
    };

    // Intersection Observer configuration
    const observerOptions = {
        root: null,
        rootMargin: '100px', // Start initializing before it comes into view
        threshold: 0.1
    };

    const carouselObserver = new IntersectionObserver((entries, observer) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                initCarousel();
                observer.unobserve(entry.target);
            }
        });
    }, observerOptions);

    carouselObserver.observe(carousel);
});

// Parallax Scrolling for Hero Image
document.addEventListener('DOMContentLoaded', function () {
    const heroSection = document.querySelector('.hero-section');
    if (!heroSection) return;

    const heroImage = heroSection.querySelector('.hero-image');
    if (!heroImage) return;

    window.addEventListener('scroll', function () {
        const scrolled = window.pageYOffset;
        const heroHeight = heroSection.offsetHeight;

        // Only apply parallax while hero is visible
        if (scrolled <= heroHeight) {
            // Move image slower than scroll (0.3 speed creates subtle parallax effect)
            const parallaxSpeed = 0.3;
            heroImage.style.transform = `translateY(${scrolled * parallaxSpeed}px)`;
        }
    });
});

// Animated Details/Summary Dropdowns
document.addEventListener('DOMContentLoaded', function () {
    const detailsElements = document.querySelectorAll('.modalities details');

    detailsElements.forEach(details => {
        const summary = details.querySelector('summary');
        const content = details.querySelector('.details-body');

        if (!summary || !content) return;

        // Set initial state
        content.style.maxHeight = '0';
        content.style.overflow = 'hidden';
        content.style.transition = 'max-height 0.3s ease-out, opacity 0.3s ease-out, padding 0.3s ease-out';
        content.style.opacity = '0';

        summary.addEventListener('click', function (e) {
            e.preventDefault();

            if (details.open) {
                // Closing
                content.style.maxHeight = '0';
                content.style.opacity = '0';
                content.style.paddingTop = '0';
                content.style.paddingBottom = '0';

                setTimeout(() => {
                    details.open = false;
                }, 300);
            } else {
                // Opening
                details.open = true;
                content.style.maxHeight = content.scrollHeight + 40 + 'px';
                content.style.opacity = '1';
                content.style.paddingTop = '1rem';
                content.style.paddingBottom = '1.5rem';
            }
        });
    });
});
