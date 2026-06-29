let isNavbarListenerAdded = false;

const renderNavbar = async () => {
    const navbarContainer = document.getElementById('navbar-container');
    if (!navbarContainer) return;

    let userData = { logged_in: false };
    try {
        const res = await fetch('/api/v1/auth/me', { credentials: 'same-origin' });
        userData = await res.json();
    } catch (e) {
        console.error('Gagal mengambil status login:', e);
    }

    let authSection = "";
    if (userData.logged_in) {
        authSection = `
            <div style="display: flex; align-items: center; gap: 15px; padding-left: 20px; border-left: 1px solid var(--border);">
                <div style="text-align: right;">
                    <div style="font-size: 12px; color: var(--text-muted);">Halo,</div>
                    <div style="font-size: 14px; font-weight: 700; color: var(--primary);">${userData.user.username}!</div>
                </div>
                <button onclick="handleLogout()" style="background: var(--bg-section); color: var(--primary); border: 1px solid var(--border); padding: 8px 16px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 13px; transition: all 0.2s;" onmouseover="this.style.background='var(--primary)'; this.style.color='white'" onmouseout="this.style.background='var(--bg-section)'; this.style.color='var(--primary)'">
                    Keluar
                </button>
            </div>
        `;
    } else {
        authSection = `
            <div style="padding-left: 20px; border-left: 1px solid var(--border);">
                <a href="/login" style="background: var(--accent); color: white; padding: 10px 24px; border-radius: 8px; font-weight: 700; text-decoration: none; font-size: 14px; transition: background 0.2s;" onmouseover="this.style.background='var(--accent-hover)'" onmouseout="this.style.background='var(--accent)'">
                    Masuk
                </a>
            </div>
        `;
    }

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
                    <nav class="nav" style="display: flex; gap: 20px;">
                        <a href="/keranjang" class="nav-link auth-check" data-target="/keranjang" style="display: flex; align-items: center; font-size: 15px; font-weight: 600; color: var(--text-main); text-decoration: none; position: relative;">
                            <i class="fas fa-shopping-cart" style="margin-right: 8px; font-size: 18px;"></i> Keranjang 
                            <span id="navCartCount" style="position: absolute; top: -8px; right: -12px; background-color: var(--accent); color: white; border-radius: 50%; padding: 2px 6px; font-size: 10px; display: none; font-weight: bold;">0</span>
                        </a>
                    </nav>
                    ${authSection}
                </div>
            </div>
        </header>
    `;

    ensureAuthModal();

    if (!isNavbarListenerAdded) {
        document.addEventListener('click', async (e) => {
            const link = e.target.closest('a') || e.target.closest('button');
            if (!link) return;

            const href = link.getAttribute('href') || link.getAttribute('data-target') || "";
            const isProtected = link.classList.contains('auth-check') || 
                                ['/keranjang', '/virtual-tailor'].some(path => href.includes(path));

            if (isProtected) {
                e.preventDefault();
                try {
                    const res = await fetch('/api/v1/auth/me', { credentials: 'same-origin' });
                    const data = await res.json();
                    if (data.logged_in) {
                        const targetUrl = link.getAttribute('data-target') || link.getAttribute('href');
                        if (targetUrl && targetUrl !== 'javascript:void(0)') window.location.href = targetUrl;
                    } else {
                        showAuthModal();
                    }
                } catch (err) {
                    showAuthModal(); 
                }
            }
        });
        isNavbarListenerAdded = true;
    }

    if (userData.logged_in) {
        fetch('/api/v1/cart', { credentials: 'same-origin' })
            .then(res => res.json())
            .then(data => {
                if (data.success && data.items && data.items.length > 0) {
                    const badge = document.getElementById('navCartCount');
                    if (badge) {
                        badge.innerText = data.items.length;
                        badge.style.display = 'inline-block';
                    }
                }
            })
            .catch(e => console.error('Error fetching cart count:', e));
    }
};

/**
 * Fungsi untuk menyuntikkan HTML Modal ke dalam Body
 */
function ensureAuthModal() {
    if (document.getElementById('authModal')) return;

    const modalHTML = `
        <div id="authModal" style="display:none; position:fixed; inset:0; z-index:9999; background:rgba(51,35,35,0.7); backdrop-filter:blur(5px); align-items:center; justify-content:center;">
            <div style="background:var(--white); width:90%; max-width:400px; padding:35px; border-radius:24px; text-align:center; box-shadow:var(--shadow-lg); border:1px solid var(--border); animation: modalFadeIn 0.3s cubic-bezier(0.34, 1.56, 0.64, 1);">
                <div style="width:70px; height:70px; background:var(--bg-section); color:var(--accent); border-radius:50%; display:flex; align-items:center; justify-content:center; margin:0 auto 20px; font-size:28px; border: 2px solid var(--border);">
                    <i class="fas fa-lock"></i>
                </div>
                <h3 style="color:var(--primary); margin-bottom:12px; font-weight:800; font-size: 22px;">Akses Terbatas</h3>
                <p style="color:var(--text-light); font-size:14px; line-height:1.7; margin-bottom:30px; padding: 0 10px;">
                    Fitur <b>Virtual Tailor</b> dan <b>Keranjang</b> memerlukan akun. Silakan masuk untuk pengalaman belanja yang lebih personal.
                </p>
                <div style="display:flex; flex-direction:column; gap:12px;">
                    <a href="/login" style="background:var(--primary); color:white; padding:14px; border-radius:12px; font-weight:700; text-decoration:none; display:flex; align-items:center; justify-content:center; transition: background 0.2s;" onmouseover="this.style.background='var(--primary-light)'" onmouseout="this.style.background='var(--primary)'">
                        Masuk ke Akun
                    </a>
                    <button onclick="closeAuthModal()" style="background:none; border:none; color:var(--text-muted); font-size:13px; font-weight:600; cursor:pointer; padding:10px; transition: color 0.2s;" onmouseover="this.style.color='var(--primary)'" onmouseout="this.style.color='var(--text-muted)'">
                        Mungkin Nanti
                    </button>
                </div>
            </div>
        </div>
        <style>
            @keyframes modalFadeIn {
                from { opacity: 0; transform: scale(0.9) translateY(30px); }
                to { opacity: 1; transform: scale(1) translateY(0); }
            }
        </style>
    `;
    document.body.insertAdjacentHTML('beforeend', modalHTML);

    // Menutup modal jika klik di area luar (backdrop)
    window.addEventListener('click', (e) => {
        const modal = document.getElementById('authModal');
        if (e.target === modal) closeAuthModal();
    });
}

function showAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) modal.style.display = 'flex';
}

function closeAuthModal() {
    const modal = document.getElementById('authModal');
    if (modal) modal.style.display = 'none';
}

/**
 * Fungsi Logout
 */
async function handleLogout() {
    if (confirm("Apakah Anda yakin ingin keluar?")) {
        const res = await fetch('/api/v1/auth/logout', { method: 'POST' });
        const data = await res.json();
        if (data.success) {
            window.location.href = '/';
        }
    }
}

// Inisialisasi
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', renderNavbar);
} else {
    renderNavbar();
}