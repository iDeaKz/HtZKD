// app/assets/custom.js

// Example: Display alert on page load
document.addEventListener('DOMContentLoaded', function() {
    console.log('H(t) Zkaedi Healing Solution Dashboard Loaded');
});

// Toggle Navbar on Mobile
document.addEventListener('DOMContentLoaded', function() {
    var toggler = document.getElementById('navbar-toggler');
    var collapse = document.getElementById('navbar-collapse');

    toggler.addEventListener('click', function() {
        collapse.classList.toggle('show');
    });
});

// Smooth Scrolling for Internal Links
document.querySelectorAll('a[href^="#"]').forEach(anchor => {
    anchor.addEventListener('click', function(e) {
        e.preventDefault();
        document.querySelector(this.getAttribute('href')).scrollIntoView({
            behavior: 'smooth'
        });
    });
});
