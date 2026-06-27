import base64
import numpy as np
import cv2
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

# Definisi Blueprint dengan Prefix Tunggal
api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

# Inisialisasi Repositori
history_repo = HistoryRepository()

# ============ HELPER ============
def decode_base64_image(base64_string):
    try:
        if ',' in base64_string:
            base64_string = base64_string.split(',')[1]
        img_data = base64.b64decode(base64_string)
        nparr = np.frombuffer(img_data, np.uint8)
        return cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    except:
        return None

# ============ PRODUCT ENDPOINTS ============

@api_bp.route('/products', methods=['GET'])
def get_products():
    product_repo = ProductRepository()
    try:
        products = product_repo.get_all_products()
        products_data = []
        for p in products:
            sc = p.size_charts[0] if p.size_charts else None
            products_data.append({
                "id": p.id_product,
                "name": p.nama_produk,
                "description": p.deskripsi,
                "price": float(p.harga),
                "image_url": p.gambar_url,
                "ld": sc.ld_produk if sc else "—",
                "panjang": sc.panjang_produk if sc else "—"
            })
        return jsonify({'success': True, 'products': products_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    product_repo = ProductRepository()
    try:
        product = product_repo.get_product_by_id(product_id)
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        sc = product.size_charts[0] if product.size_charts else None
        product_data = {
            "id": product.id_product,
            "name": product.nama_produk,
            "description": product.deskripsi,
            "price": float(product.harga),
            "image_url": product.gambar_url,
            "size_charts": [{"ld_produk": sc.ld_produk, "panjang_produk": sc.panjang_produk}] if sc else []
        }
        return jsonify({'success': True, 'product': product_data}), 200
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

# ============ SESSION PRODUCT (VIRTUAL TAILOR START) ============

@api_bp.route('/session/product', methods=['POST'])
def select_product():
    product_repo = ProductRepository()
    data = request.get_json() or {}
    product_id = data.get('product_id')
    product = product_repo.get_product_by_id(product_id)
    if not product: return jsonify({'error': 'Product not found'}), 404
        
    target_size = product.size_charts[0].ld_produk if product.size_charts else 100.0
    session['selected_product'] = {
        "id": product.id_product,
        "name": product.nama_produk,
        "target_dress_size_cm": target_size,
        "image_url": product.gambar_url
    }
    return jsonify({'success': True, 'message': f"Selected {product.nama_produk}"}), 200

@api_bp.route('/session/product', methods=['GET'])
def get_selected_product():
    product = session.get('selected_product')
    return jsonify({'success': True, 'product': product}), 200


# ============ CART ENDPOINTS (LOGIN REQUIRED) ============

@api_bp.route('/cart', methods=['POST'])
@login_required
def add_to_cart():
    cart_repo = CartRepository()
    try:
        data = request.get_json()
        product_id = data.get('product_id')
        
        # MENGAMBIL DATA AI DARI FRONTEND
        fit_status = data.get('fit_status')
        body_shape = data.get('body_shape')

        if not product_id: 
            return jsonify({"success": False, "message": "ID Produk kosong"}), 400
        
        # MENYIMPAN KE REPOSITORY BESERTA HASIL AI
        cart_repo.add_to_cart(
            id_user=current_user.id_user, 
            id_product=product_id,
            fit_status=fit_status,
            body_shape=body_shape
        )
        return jsonify({"success": True, "message": "Berhasil disimpan"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@api_bp.route('/cart', methods=['GET'])
@login_required
def get_cart_items():
    cart_repo = CartRepository()
    items = cart_repo.get_user_cart(current_user.id_user)
    cart_data = []
    for i in items:
        cart_data.append({
            "id_cart": i.id_cart,
            "fit_status": i.fit_status,
            "body_shape": i.body_shape,
            "product": {
                "id": i.product.id_product,
                "name": i.product.nama_produk,
                "price": float(i.product.harga),
                "image_url": i.product.gambar_url,
                "category": "Pakaian" # Fallback karena di db_models Anda belum ada atribut kategori
            }
        })
    return jsonify({"success": True, "items": cart_data}), 200

@api_bp.route('/cart/order', methods=['POST'])
@login_required
def convert_cart():
    cart_repo = CartRepository()
    try:
        # Tandai di DB bahwa user ini 'Checkout' (pindah ke Shopee/Admin)
        cart_repo.mark_as_ordered(current_user.id_user)
        return jsonify({"success": True, "message": "Status pesanan dicatat"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

# Endpoint untuk menghapus barang dari keranjang
@api_bp.route('/cart/<int:cart_id>', methods=['DELETE'])
@login_required
def remove_from_cart(cart_id):
    from infrastructure.models.db_models import Cart
    from extensions import db
    try:
        # Pastikan item tersebut adalah milik user yang sedang login
        item = Cart.query.filter_by(id_cart=cart_id, id_user=current_user.id_user).first()
        if not item:
            return jsonify({"success": False, "message": "Data tidak ditemukan"}), 404
            
        db.session.delete(item)
        db.session.commit()
        return jsonify({"success": True, "message": "Barang dihapus"}), 200
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500
    

# ============ AI ANALYSIS ENDPOINTS ============

@api_bp.route('/prescan', methods=['POST'])
def prescan():
    data = request.get_json() or {}
    img = decode_base64_image(data.get('image', ''))
    if img is None: return jsonify({'error': 'Invalid image'}), 400
        
    try:
        result = pose_service.pose_detector.detect(img)
        landmarks = pose_service.pose_detector.get_landmarks(result)
        if landmarks is None:
            return jsonify({'success': True, 'aligned ': False, 'message': 'Tubuh tidak terdeteksi'}), 200
            
        aligned = pose_service.pose_detector.are_shoulders_hips_visible(landmarks)
        feet_visible = landmarks[27].visibility > 0.5 or landmarks[28].visibility > 0.5

        return jsonify({'success': True, 'aligned': aligned and feet_visible, 'message': 'Posisi tegak' if (aligned and feet_visible) else 'Pastikan kaki terlihat di kamera'}), 200
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analyze', methods=['POST'])
@login_required
def analyze():
    try:
        product = session.get('selected_product')
        if not product: return jsonify({'error': 'Pilih produk terlebih dahulu'}), 400
            
        data = request.get_json()
        image_b64 = data.get('image', '').split(',')[1] if ',' in data.get('image', '') else data.get('image', '')
        u_height = data.get('user_height_cm')
        if not u_height:
            return jsonify({'error': 'Input tinggi badan diperlukan'}), 400
        
        analysis_request = PoseAnalysisRequest(
            image_bytes=base64.b64decode(image_b64),
            calibration_type=CalibrationType.HEIGHT,
            calibration_value_cm=float(u_height),
            user_height_cm=float(u_height),
            dress_size_cm=product['target_dress_size_cm']
        )
        
        measurements, error = pose_service.analyze(analysis_request)
        if error: return jsonify({'error': error}), 400

        if measurements:
            try:
                # Catat aktivitas ke tabel user_history melalui Repository
                history_repo.log_activity(
                    id_user=current_user.id_user,
                    id_product=product['id'],
                    fit_status=measurements.fit_recommendation,
                    body_shape=measurements.body_shape
                )
                print(f">>> HISTORY SAVED: User {current_user.username} scanned {product['name']}")
            except Exception as e:
                # Jangan biarkan error simpan history membatalkan respon AI ke user
                print(f">>> HISTORY ERROR: {str(e)}")
        
        return jsonify({
            'success': True,
            'measurements': measurements.to_dict(),
            'product_target_size': product['target_dress_size_cm']
        }), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy'}), 200

def cleanup():
    pose_service.close()