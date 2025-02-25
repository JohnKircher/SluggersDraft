document.addEventListener('DOMContentLoaded', function () {
    // Add hover effects to buttons
    const buttons = document.querySelectorAll('.team-button, .player-button, .back-button');
    buttons.forEach(button => {
        button.addEventListener('mouseenter', function () {
            this.style.transform = 'scale(1.05)';
        });
        button.addEventListener('mouseleave', function () {
            this.style.transform = 'scale(1)';
        });
    });
});