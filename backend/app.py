from flask import Flask, send_from_directory, jsonify
from flask_cors import CORS
import os
from pathlib import Path

def create_app():
    app = Flask(__name__)
    from extensions import db
    
    # Configuration
    app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
    app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'virtual-tailor-super-secret-key-123')
    
    # Database Configuration
    db_user = os.environ.get('DB_USER', 'root')
    db_pass = os.environ.get('DB_PASS', '')
    db_host = os.environ.get('DB_HOST', 'localhost')
    db_name = os.environ.get('DB_NAME', 'db_vinci_store')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'mysql+pymysql://{db_user}:{db_pass}@{db_host}/{db_name}'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    
    # Initialize extensions
    db.init_app(app)
    
    # Enable CORS for all routes with proper settings
    CORS(app, origins=['*'], supports_credentials=True, methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'])
    
    # Register blueprints
    from interfaces.api.routes import api_bp, cleanup
    app.register_blueprint(api_bp)
    
    # Serve static files (HTML test pages)
    @app.route('/')
    def root():
        return send_from_directory('static', 'index.html')
        
    @app.route('/product/<int:product_id>')
    def product_page(product_id):
        return send_from_directory('static', 'product_detail.html')
    
    @app.route('/virtual-tailor')
    def virtual_tailor_page():
        return send_from_directory('static', 'virtual_tailor.html')
        
    @app.route('/keranjang')
    def keranjang_page():
        return send_from_directory('static', 'keranjang.html')
    
    @app.route('/static/<path:filename>')
    def serve_static(filename):
        return send_from_directory('static', filename)
    
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
                'test_page': 'GET /webcam'
            }
        })
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

      API Endpoints:
      GET  /api/v1/products          - Get mock product catalog
      POST /api/v1/session/product   - Set target product in session
      POST /api/v1/prescan           - Fast pose alignment check
      POST /api/v1/analyze           - Final analysis (WebRTC/Upload)

      Press Ctrl+C to stop
    =========================================================================
    """)
    
    app.run(host='0.0.0.0', port=port, debug=debug)