import base64
import numpy as np
import cv2
import traceback
from flask import Blueprint, request, jsonify, session
from pathlib import Path
from flask_login import current_user, login_required

# Import DTO & Service
from application.dto.pose_analysis_request import PoseAnalysisRequest, CalibrationType
from application.services.pose_analysis_service import PoseAnalysisService

# Import Repositories
from infrastructure.repositories.cart_repository import CartRepository
from infrastructure.repositories.history_repository import HistoryRepository
from infrastructure.repositories.product_repository import ProductRepository

# Setup AI Service
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
pose_service = PoseAnalysisService(MODELS_DIR)

# Definisi Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# ============ HELPER ============
def decode_base64_image(base64_string):
    """Helper to decode base64 string from data URL"""
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        return img
    except Exception as e:
        print(f"Base64 decode error: {e}")
        return None

# ============ PRODUCT ENDPOINTS ============

@api_bp.route('/products', methods=['GET'])
def get_products():
    # Gunakan variabel lokal 'repo' agar tidak bentrok dengan nama Class
    repo = ProductRepository()
    try:
        products = repo.get_active_products()
        products_data = []
        for p in products:
            # Ambil size chart pertama
            sc = p.size_charts[0] if p.size_charts else None
            products_data.append({
                "id": p.id_product,
                "name": p.nama_produk,
                "description": p.deskripsi,
                "price": float(p.harga) if p.harga else 0.0,
                "image_url": p.gambar_url,
                # FIX: Flattening data agar Frontend gampang baca LD & Panjang
                "ld": sc.ld_produk if sc else "—",
                "panjang": sc.panjang_produk if sc else "—",
                "status": p.status
            })
        return jsonify({'success': True, 'products': products_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    repo = ProductRepository()
    try:
        product = repo.get_product_by_id(product_id)
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        sc = product.size_charts[0] if product.size_charts else None
        
        # Format data detail dengan struktur datar (flat)
        product_data = {
            "id": product.id_product,
            "name": product.nama_produk,
            "description": product.deskripsi,
            "price": float(product.harga) if product.harga else 0.0,
            "image_url": product.gambar_url,
            "ld": sc.ld_produk if sc else "—",
            "panjang": sc.panjang_produk if sc else "—",
            "size_charts": [{"ld_produk": sc.ld_produk, "panjang_produk": sc.panjang_produk}] if sc else []
        }
        return jsonify({'success': True, 'product': product_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ SESSION MANAGEMENT ============

@api_bp.route('/session/product', methods=['POST'])
def select_product():
    repo = ProductRepository()
    try:
        data = request.get_json() or {}
        product_id = data.get('product_id')
        product = repo.get_product_by_id(product_id)
        
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404
            
        sc = product.size_charts[0] if product.size_charts else None
        
        # Simpan detail lengkap ke session
        session['selected_product'] = {
            "id": product.id_product,
            "name": product.nama_produk,
            "price": float(product.harga) if product.harga else 0.0,
            "target_dress_size_cm": sc.ld_produk if sc else 100.0,
            "image_url": product.gambar_url
        }
        session.modified = True
        
        return jsonify({'success': True, 'message': f"Selected {product.nama_produk}"}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/session/product', methods=['GET'])
def get_selected_product():
    product = session.get('selected_product')
    return jsonify({'success': True, 'product': product}), 200

# ============ CART ENDPOINTS (LOGIN REQUIRED) ============

@api_bp.route('/cart', methods=['POST'])
@login_required
def add_to_cart():
    repo = CartRepository()
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        fit = data.get('fit_status')
        shape = data.get('body_shape')

        if not product_id:
            return jsonify({"success": False, "message": "ID Produk kosong"}), 400

        repo.add_to_cart(
            id_user=current_user.id_user, 
            id_product=product_id, 
            fit_status=fit, 
            body_shape=shape
        )
        return jsonify({"success": True, "message": "Barang berhasil masuk keranjang"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/cart', methods=['GET'])
@login_required
def get_cart_items():
    repo = CartRepository()
    try:
        items = repo.get_user_cart(current_user.id_user)
        cart_data = []
        for i in items:
            cart_data.append({
                "id_cart": i.id_cart,
                "fit_status": i.fit_status,
                "body_shape": i.body_shape,
                "product": {
                    "id": i.product.id_product,
                    "name": i.product.nama_produk,
                    "price": float(i.product.harga) if i.product.harga else 0.0,
                    "image_url": i.product.gambar_url,
                    "category": "Pakaian"
                }
            })
        return jsonify({"success": True, "items": cart_data}), 200
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@api_bp.route('/cart/order', methods=['POST'])
@login_required
def order_cart():
    repo = CartRepository()
    try:
        repo.mark_as_ordered(current_user.id_user)
        return jsonify({"success": True, "message": "Pesanan dicatat"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/cart/<int:cart_id>', methods=['DELETE'])
@login_required
def remove_from_cart(cart_id):
    from extensions import db
    from infrastructure.models.db_models import Cart
    try:
        item = Cart.query.filter_by(id_cart=cart_id, id_user=current_user.id_user).first()
        if item:
            db.session.delete(item)
            db.session.commit()
            return jsonify({"success": True}), 200
        return jsonify({"success": False, "message": "Item not found"}), 404
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ============ AI ANALYSIS ENDPOINTS ============

@api_bp.route('/prescan', methods=['POST'])
def prescan():
    """Fast check if pose is aligned correctly within ROI"""
    data = request.get_json() or {}
    image_b64 = data.get('image')
    if not image_b64:
        return jsonify({'error': 'No image provided'}), 400
        
    img = decode_base64_image(image_b64)
    if img is None:
        return jsonify({'error': 'Invalid image format'}), 400
        
    try:
        # Detect pose via MediaPipe
        result = pose_service.pose_detector.detect(img)
        landmarks = pose_service.pose_detector.get_landmarks(result)
        
        if landmarks is None:
            return jsonify({
                'success': True,
                'aligned': False,
                'message': 'Tubuh tidak terdeteksi'
            }), 200
            
        # Check if vital points are visible
        shoulders_hips = pose_service.pose_detector.are_shoulders_hips_visible(landmarks)
        # Check feet visibility for height accuracy
        feet_visible = landmarks[27].visibility > 0.5 or landmarks[28].visibility > 0.5
        
        is_aligned = shoulders_hips and feet_visible
        
        return jsonify({
            'success': True,
            'aligned': is_aligned,
            'message': 'Pose Sesuai' if is_aligned else 'Pastikan seluruh tubuh hingga kaki terlihat'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analyze', methods=['POST'])
@login_required
def analyze():
    """Analyze image and return measurements based on session product"""
    try:
        # Handle Base64 (WebRTC) or Multipart File (Upload)
        if request.is_json:
            data = request.get_json()
            image_b64 = data.get('image')
            if not image_b64: return jsonify({'error': 'No image'}), 400
            if ',' in image_b64: image_b64 = image_b64.split(',')[1]
            image_bytes = base64.b64decode(image_b64)
            u_height = float(data.get('user_height_cm', 165))
            product_id = data.get('product_id')
        else:
            if 'image' not in request.files: return jsonify({'error': 'No file'}), 400
            image_bytes = request.files['image'].read()
            u_height = float(request.form.get('user_height_cm', 165))
            product_id = request.form.get('product_id')
            
        if not product_id:
            return jsonify({'error': 'Pilih produk terlebih dahulu di halaman detail'}), 400
            
        repo = ProductRepository()
        product = repo.get_product_by_id(product_id)
        if not product:
            return jsonify({'error': 'Produk tidak ditemukan'}), 404
            
        sc = product.size_charts[0] if product.size_charts else None
        dress_size = float(sc.ld_produk) if sc else 100.0
        
        # Build AI Request
        analysis_request = PoseAnalysisRequest(
            image_bytes=image_bytes,
            calibration_type=CalibrationType.HEIGHT,
            calibration_value_cm=u_height,
            user_height_cm=u_height,
            dress_size_cm=dress_size
        )
        
        # RUN AI CORE
        measurements, error = pose_service.analyze(analysis_request)
        
        if error:
            return jsonify({'error': error}), 400
        
        # LOG KE USER HISTORY UNTUK ADMIN DASHBOARD
        try:
            h_repo = HistoryRepository()
            h_repo.log_activity(
                id_user=current_user.id_user,
                id_product=product.id_product,
                fit_status=measurements.fit_recommendation,
                body_shape=measurements.body_shape
            )
        except Exception as log_e:
            print(f"Logging history failed: {log_e}")
        
        return jsonify({
            'success': True,
            'measurements': measurements.to_dict(),
            'product_target_size': dress_size
        }), 200
        
    except Exception as e:
        traceback.print_exc()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'virtual-tailor'}), 200

def cleanup():
    pose_service.close()