from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os
from pathlib import Path
from flask_login import login_required
from dotenv import load_dotenv
load_dotenv() 

# Import Extensions, Blueprint, dan Model
from extensions import db, login_manager
from interfaces.api.auth_routes import auth_bp
from interfaces.api.admin_routes import admin_bp
from infrastructure.models.db_models import User
from infrastructure.security.decorators import admin_required

def create_app():
    app = Flask(__name__)
    
    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'virtual-tailor-super-secret-key-123')
    
    # Konfigurasi Keamanan Sesi (Wajib untuk Flask-Login & Hosting)
    app.config['SESSION_COOKIE_HTTPONLY'] = True
    app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
    app.config['SESSION_COOKIE_SECURE'] = False # True saat hosting dengan HTTPS
    
    # Database Configuration
    db_user = os.environ.get('DB_USER', 'root')
    db_pass = os.environ.get('DB_PASS', '')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME', 'db_vinci_store')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

    # Mencegah Database Timeout (Gagal Memuat Produk)
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle': 280,
        'pool_size': 20,
        'max_overflow': 30,
        'pool_timeout': 30
    }
    
    # Initialize extensions
    db.init_app(app)
    login_manager.init_app(app) # <-- INISIALISASI LOGIN MANAGER
    
    # Konfigurasi Flask-Login
    login_manager.login_view = 'login_page'
    login_manager.login_message = "Silakan login terlebih dahulu untuk melanjutkan."

    # User Loader untuk mengambil data user dari session cookie
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))
    
    # Enable CORS for all routes with proper settings
    CORS(app, origins=['*'], supports_credentials=True, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Register blueprints
    from interfaces.api.routes import api_bp
    app.register_blueprint(auth_bp) 
    app.register_blueprint(api_bp)
    app.register_blueprint(admin_bp)

    # ==========================================
    # SERVE STATIC FILES (HTML PAGES)
    # ==========================================
    @app.route('/')
    def root():
        return send_from_directory(app.static_folder, 'index.html')
        
    @app.route('/product/<int:product_id>')
    def product_page(product_id):
        return send_from_directory(app.static_folder, 'product_detail.html')
    
    @app.route('/virtual-tailor')
    @login_required
    def virtual_tailor_page():
        return send_from_directory(app.static_folder, 'virtual_tailor.html')
        
    @app.route('/keranjang')
    @login_required
    def keranjang_page():
        return send_from_directory(app.static_folder, 'keranjang.html')
    
    @app.route('/register')
    def register_page():
        return send_from_directory(app.static_folder, 'register.html')
    
    @app.route('/login')
    def login_page():
        return send_from_directory(app.static_folder, 'login.html')
    
    from extensions import oauth
    oauth.init_app(app)
    oauth.register(
        name='google',
        client_id=os.environ.get('GOOGLE_CLIENT_ID'),
        client_secret=os.environ.get('GOOGLE_CLIENT_SECRET'),
        server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
        client_kwargs={'scope': 'openid email profile'}
    )

    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory(app.static_folder, filename)
    
    @app.route('/admin/dashboard')
    @login_required
    @admin_required
    def admin_dashboard():
        return send_from_directory(os.path.join(app.static_folder, 'admin'), 'dashboard.html')
    
    @app.route('/admin/products')
    @login_required
    @admin_required
    def admin_manage_products():
        return send_from_directory(os.path.join(app.static_folder, 'admin'), 'manage_products.html')

    @app.route('/admin/users')
    @login_required
    @admin_required
    def admin_users():
        return send_from_directory(os.path.join(app.static_folder, 'admin'), 'users.html')

    @app.route('/admin/scans')
    @login_required
    @admin_required
    def admin_scans():
        return send_from_directory(os.path.join(app.static_folder, 'admin'), 'scans.html')

    @app.route('/admin/carts')
    @login_required
    @admin_required
    def admin_carts():
        return send_from_directory(os.path.join(app.static_folder, 'admin'), 'carts.html')

    # API info
    @app.route('/api')
    def api_info():
        return jsonify({
            'service': 'Virtual Tailor API',
            'version': '1.0.0',
            'endpoints': {
                'health': '/api/v1/health',
                'analyze': 'POST /api/v1/analyze (upload image)',
                'webcam_start': 'POST /api/v1/webcam/start',
                'webcam_frame': 'GET /api/v1/webcam/frame',
                'webcam_analyze': 'POST /api/v1/webcam/analyze',
                'webcam_calibrate': 'POST /api/v1/webcam/calibrate',
                'webcam_stop': 'POST /api/v1/webcam/stop',
                'test_page': 'GET /webcam',
                'auth_register': 'POST /api/v1/register',
                'auth_login': 'POST /api/v1/login',
                'auth_logout': 'POST /api/v1/logout',
                'auth_me': 'GET /api/v1/me'
            }
        })
    # Pastikan Sesi Database Selalu Ditutup Setelah Request Selesai
    @app.teardown_appcontext
    def shutdown_session(exception=None):
        db.session.remove()
    return app

if __name__ == '__main__':
    app = create_app()
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Create static folder if not exists
    static_dir = Path(__file__).parent / 'static'
    static_dir.mkdir(exist_ok=True)
    
    print(f"""
    =========================================================================
                       VIRTUAL TAILOR API - READY
    =========================================================================
      Server running on: http://localhost:{port}

      BROWSER APP: http://localhost:{port}/
      LOGIN PAGE : http://localhost:{port}/login

      API Endpoints:
      GET  /api/v1/products          - Get mock product catalog
      POST /api/v1/session/product   - Set target product in session
      POST /api/v1/analyze           - Final analysis (WebRTC/Upload)
      POST /api/v1/register          - User Registration
      POST /api/v1/login             - User Login

      Press Ctrl+C to stop
    =========================================================================
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)