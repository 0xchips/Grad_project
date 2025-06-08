// Sidebar toggle functionality
document.addEventListener('DOMContentLoaded', function() {
    // Restore sidebar state immediately to prevent flash
    restoreSidebarState();
    initializeSidebarToggle();
    addTooltipsToSidebar();
});

// Restore sidebar state before page fully loads to prevent flash
function restoreSidebarState() {
    const sidebar = document.querySelector('.sidebar');
    const savedState = localStorage.getItem('sidebarCollapsed');
    
    if (sidebar) {
        // Disable transitions during initial load
        sidebar.classList.add('no-transition');
        
        if (savedState === 'true') {
            sidebar.classList.add('collapsed');
        }
        
        // Re-enable transitions after a short delay
        setTimeout(() => {
            sidebar.classList.remove('no-transition');
        }, 100);
    }
}

function initializeSidebarToggle() {
    const sidebar = document.querySelector('.sidebar');
    const toggleBtn = document.querySelector('.sidebar-toggle');
    
    if (toggleBtn && sidebar) {
        // Remove any existing event listeners to prevent duplicates
        toggleBtn.replaceWith(toggleBtn.cloneNode(true));
        const newToggleBtn = document.querySelector('.sidebar-toggle');
        
        newToggleBtn.addEventListener('click', function(e) {
            e.preventDefault();
            e.stopPropagation();
            
            sidebar.classList.toggle('collapsed');
            
            // Save state to localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        });
    }
}

function addTooltipsToSidebar() {
    // Add tooltips to navigation links if they don't already have them
    const navLinks = document.querySelectorAll('.sidebar nav ul li a');
    
    navLinks.forEach(link => {
        if (!link.hasAttribute('data-tooltip')) {
            const span = link.querySelector('span');
            if (span) {
                link.setAttribute('data-tooltip', span.textContent.trim());
            }
        }
    });
}

// Add keyboard shortcut for sidebar toggle (Ctrl/Cmd + B)
document.addEventListener('keydown', function(e) {
    if ((e.ctrlKey || e.metaKey) && e.key === 'b') {
        e.preventDefault();
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            sidebar.classList.toggle('collapsed');
            
            // Save state to localStorage
            const isCollapsed = sidebar.classList.contains('collapsed');
            localStorage.setItem('sidebarCollapsed', isCollapsed);
        }
    }
});

// Early restoration to prevent flash - runs as soon as the script loads
(function() {
    // Wait for sidebar element to be available
    function waitForSidebar() {
        const sidebar = document.querySelector('.sidebar');
        if (sidebar) {
            // Disable transitions immediately
            sidebar.classList.add('no-transition');
            
            const savedState = localStorage.getItem('sidebarCollapsed');
            if (savedState === 'true') {
                sidebar.classList.add('collapsed');
            }
            
            // Re-enable transitions after DOM is ready
            setTimeout(() => {
                sidebar.classList.remove('no-transition');
            }, 150);
        } else {
            // If sidebar not found, try again in next frame
            requestAnimationFrame(waitForSidebar);
        }
    }
    waitForSidebar();
})();
