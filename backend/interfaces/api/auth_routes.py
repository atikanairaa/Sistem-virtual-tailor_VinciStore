import re
from flask import Blueprint, request, jsonify, session, redirect, url_for
from flask_login import login_user, logout_user, login_required, current_user
from application.services.auth_service import AuthService
from extensions import oauth

auth_bp = Blueprint('auth_bp', __name__, url_prefix='/api/v1/auth')
auth_service = AuthService()

@auth_bp.route('/register', methods=['POST'])
def register():
    # Ambil data JSON dari frontend
    data = request.get_json()
    if not data:
        return jsonify({"success": False, "message": "Data tidak valid"}), 400

    username = data.get('username')
    email = data.get('email')
    password = data.get('password')
    phone = data.get('phone')

    # Validasi input kosong
    if not username or not email or not password:
        return jsonify({"success": False, "message": "Username, email, dan password wajib diisi"}), 400

    # Panggil service
    user, error = auth_service.register(username, email, password, phone)
    
    if error:
        return jsonify({"success": False, "message": error}), 400
        
    return jsonify({
        "success": True, 
        "message": "Registrasi berhasil! Silakan login."
    }), 201

@auth_bp.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    email = data.get('email')
    password = data.get('password')

    if not email or not password:
        return jsonify({"success": False, "message": "Email dan password wajib diisi"}), 400

    user, error = auth_service.verify_login(email, password)
    
    if error:
        return jsonify({"success": False, "message": error}), 401

    login_user(user, remember=data.get('remember', False))

    target_url = '/admin/dashboard' if user.role == 1 else '/'
    
    # RESPONSE BERBASIS ROLE
    return jsonify({
        "success": True, 
        "message": "Login berhasil!",
        "user": {"username": user.username, "role": user.role},
        "redirect": target_url 
    }), 200

@auth_bp.route('/login/google')
def login_google():
    google = oauth.create_client('google')
    # Link redirect harus sama dengan yang di Google Console
    redirect_uri = url_for('auth_bp.authorize_google', _external=True)
    return google.authorize_redirect(redirect_uri)

@auth_bp.route('/callback')
def authorize_google():
    google = oauth.create_client('google')
    token = google.authorize_access_token()
    
    # --- PERBAIKAN DI SINI ---
    # Ambil user_info langsung dari token (Cara standar OpenID Connect)
    user_info = token.get('userinfo')
    
    # Jika karena suatu hal userinfo tidak ada di token, ambil secara manual lewat URL lengkap
    if not user_info:
        resp = google.get('https://www.googleapis.com/oauth2/v3/userinfo')
        user_info = resp.json()
    # -------------------------
    
    # Ambil data dari hasil Google
    email = user_info.get('email')
    username = user_info.get('name')
    google_id = user_info.get('sub') # 'sub' adalah ID unik permanen dari Google

    # Gunakan service untuk menangani data (cek DB atau buat akun baru)
    user, error = auth_service.handle_google_login(
        email=email,
        username=username,
        google_id=google_id
    )
    
    if user:
        # Berhasil: Buat sesi login di browser
        login_user(user)
        return redirect('/') # Kembali ke beranda
    
    # Jika gagal, kembalikan ke login dengan pesan error
    return redirect('/login?error=google_failed')

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout():
    logout_user() # Hapus sesi cookie
    return jsonify({"success": True, "message": "Logout berhasil"}), 200

@auth_bp.route('/me', methods=['GET'])
def get_current_user():
    """Endpoint untuk mengecek apakah user sedang login (untuk frontend)"""
    if current_user.is_authenticated:
        return jsonify({
            "success": True,
            "logged_in": True,
            "user": {
                "id_user": current_user.id_user,
                "username": current_user.username,
                "role": current_user.role
            }
        })
    return jsonify({"success": True, "logged_in": False})