const canvas = document.getElementById('confetti');
const ctx = canvas.getContext('2d');

canvas.width = window.innerWidth;
canvas.height = window.innerHeight;

let pieces = [];
const numberOfPieces = 50; // Heavily reduced count
const colors = ['#a855f7', '#d8b4fe', '#ffffff'];

class Confetti {
    constructor(isBurst = false) {
        this.isBurst = isBurst;
        this.x = isBurst ? canvas.width / 2 : Math.random() * canvas.width;
        this.y = isBurst ? canvas.height / 2 : Math.random() * canvas.height - canvas.height;
        this.size = Math.random() * 4 + 2;
        this.color = colors[Math.floor(Math.random() * colors.length)];
        
        if (isBurst) {
            const angle = Math.random() * Math.PI * 2;
            const velocity = Math.random() * 10 + 5;
            this.vx = Math.cos(angle) * velocity;
            this.vy = Math.sin(angle) * velocity;
        } else {
            this.vx = (Math.random() - 0.5) * 0.5;
            this.vy = Math.random() * 1 + 1;
        }
        this.gravity = 0.15;
    }

    update() {
        this.x += this.vx;
        this.y += this.vy;
        
        if (this.isBurst) {
            this.vy += this.gravity;
        }

        if (this.y > canvas.height) {
            if (this.isBurst) {
                // Remove burst particles once they leave the screen
                return false;
            }
            this.y = -20;
            this.x = Math.random() * canvas.width;
        }
        return true;
    }

    draw() {
        ctx.beginPath();
        ctx.arc(this.x, this.y, this.size, 0, Math.PI * 2);
        ctx.fillStyle = this.color;
        ctx.fill();
    }
}

function init() {
    pieces = [];
    for (let i = 0; i < numberOfPieces; i++) {
        pieces.push(new Confetti(false));
    }
}

function animate() {
    ctx.clearRect(0, 0, canvas.width, canvas.height);
    pieces = pieces.filter(p => {
        const alive = p.update();
        if (alive) p.draw();
        return alive;
    });
    
    // Maintain minimum number of background pieces
    while (pieces.filter(p => !p.isBurst).length < numberOfPieces) {
        pieces.push(new Confetti(false));
    }
    
    requestAnimationFrame(animate);
}

window.addEventListener('resize', () => {
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
});

// Start animation on specific celebratory pages
if (window.location.pathname.includes('wish.html') || window.location.pathname.includes('marriage.html')) {
    init();
    animate();
}

// Ensure celebrate is available immediately
window.celebrate = function() {
    console.log("Magic triggered!");
    for (let i = 0; i < 150; i++) {
        pieces.push(new Confetti(true));
    }
};

// Fallback: Click anywhere on the background of the wish page for magic
window.addEventListener('click', (e) => {
    if (window.location.pathname.includes('wish.html') || window.location.pathname.includes('marriage.html')) {
        // Only if clicking background or specific elements
        if (e.target.tagName === 'BODY' || e.target.classList.contains('hero-section')) {
            window.celebrate();
        }
    }
});

