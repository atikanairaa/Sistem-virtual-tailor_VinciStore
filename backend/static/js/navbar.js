const renderNavbar = () => {
    const navbarContainer = document.getElementById('navbar-container');
    if (navbarContainer) {
        navbarContainer.innerHTML = `
            <header class="header" style="background: var(--white); border-bottom: 1px solid var(--border); position: sticky; top: 0; z-index: 100; box-shadow: var(--shadow-sm);">
                <div class="container" style="display: flex; align-items: center; justify-content: space-between; height: 72px; gap: 24px;">
                    <a href="/" class="logo" style="display: flex; align-items: center; gap: 10px; font-weight: 800; font-size: 18px; letter-spacing: 3px; color: var(--primary); text-decoration: none; flex-shrink: 0;">
                        <div style="width: 36px; height: 36px; border-radius: 50%; overflow: hidden; background: var(--primary); display: flex; align-items: center; justify-content: center; border: 2px solid var(--primary-light);">
                            <img src="/static/logo.png" alt="Logo" style="width: 100%; height: 100%; object-fit: cover;">
                        </div>
                        VINCI STORE
                    </a>
                    
                    <div style="display: flex; align-items: center; gap: 24px;">
                        <div class="search-bar" style="position: relative; display: flex; align-items: center;">
                            <i class="fas fa-search" style="position: absolute; left: 14px; color: var(--text-muted); font-size: 14px;"></i>
                            <input type="text" placeholder="Cari produk..." id="searchInput" style="background: var(--bg-body); border: 1px solid var(--border); border-radius: 8px; padding: 10px 16px 10px 40px; width: 240px; font-size: 14px; color: var(--text-main); outline: none; transition: all 0.2s; font-family: var(--font);">
                        </div>
                        
                        <nav class="nav" style="display: flex; height: 100%;">
                            <a href="/keranjang" class="nav-link" style="display: flex; align-items: center; font-size: 15px; font-weight: 600; color: var(--text-main); text-decoration: none; position: relative;">
                                <i class="fas fa-shopping-cart" style="margin-right: 8px; font-size: 18px;"></i> Keranjang 
                                <span id="navCartCount" style="position: absolute; top: -8px; right: -12px; background-color: var(--accent); color: white; border-radius: 50%; padding: 2px 6px; font-size: 10px; display: none; font-weight: bold;">0</span>
                            </a>
                        </nav>
                    </div>
                </div>
            </header>
        `;

        // Highlight active link (only Keranjang is left, so if we're on /keranjang, highlight it)
        const currentPath = window.location.pathname;
        if (currentPath === '/keranjang') {
            const kLink = navbarContainer.querySelector('.nav-link');
            if(kLink) kLink.style.color = 'var(--primary)';
        }

        // Fetch cart count
        fetch('/api/v1/cart')
            .then(res => res.json())
            .then(data => {
                if(data.success && data.items && data.items.length > 0) {
                    const badge = document.getElementById('navCartCount');
                    if(badge) {
                        badge.innerText = data.items.length;
                        badge.style.display = 'inline-block';
                    }
                }
            })
            .catch(e => console.error('Error fetching cart count:', e));
    }
};

if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderNavbar);
} else {
    renderNavbar();
}
