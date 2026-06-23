import base64
import uuid
import time
import numpy as np
# pyrefly: ignore [missing-import]
import cv2
from flask import Blueprint, request, jsonify, session, Response
from pathlib import Path

from application.dto.pose_analysis_request import PoseAnalysisRequest, CalibrationType
from application.services.pose_analysis_service import PoseAnalysisService

# Initialize service
MODELS_DIR = Path(__file__).parent.parent.parent / "models"
pose_service = PoseAnalysisService(MODELS_DIR)

api_bp = Blueprint('api', __name__, url_prefix='/api/v1')

from infrastructure.repositories.product_repository import ProductRepository
product_repo = ProductRepository()

# ============ PRODUCT ENDPOINTS ============

@api_bp.route('/products', methods=['GET'])
def get_products():
    try:
        products = product_repo.get_all_products()
        products_data = []
        for p in products:
            # Assumes target dress size is derived from size chart (e.g. max LD or first size chart)
            target_size = 100.0 # Default fallback
            if p.size_charts:
                target_size = p.size_charts[0].ld_produk
                
            products_data.append({
                "id": p.id_product,
                "name": p.nama_produk,
                "category": "Clothes", # Missing category in schema, default "Clothes"
                "description": p.deskripsi,
                "price": float(p.harga),
                "target_dress_size_cm": target_size,
                "image_url": p.gambar_url
            })
        return jsonify({'success': True, 'products': products_data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/products/<int:product_id>', methods=['GET'])
def get_product(product_id):
    try:
        product = product_repo.get_product_by_id(product_id)
        if not product:
            return jsonify({'success': False, 'error': 'Product not found'}), 404

        size_chart = None
        if product.size_charts:
            sc = product.size_charts[0]
            size_chart = {
                'ld_produk': sc.ld_produk,
                'panjang_produk': sc.panjang_produk
            }

        product_data = {
            "id": product.id_product,
            "name": product.nama_produk,
            "description": product.deskripsi,
            "price": float(product.harga),
            "image_url": product.gambar_url,
            "size_chart": size_chart
        }
        return jsonify({'success': True, 'product': product_data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/session/product', methods=['POST'])
def select_product():
    data = request.get_json() or {}
    product_id = data.get('product_id')
    
    product = product_repo.get_product_by_id(product_id)
    if not product:
        return jsonify({'error': 'Product not found'}), 404
        
    target_size = 100.0
    if product.size_charts:
        target_size = product.size_charts[0].ld_produk
        
    product_dict = {
        "id": product.id_product,
        "name": product.nama_produk,
        "target_dress_size_cm": target_size,
        "image_url": product.gambar_url
    }
    session['selected_product'] = product_dict
    return jsonify({'success': True, 'message': f"Selected {product.nama_produk}"}), 200

@api_bp.route('/session/product', methods=['GET'])
def get_selected_product():
    product = session.get('selected_product')
    if not product:
        return jsonify({'success': False, 'product': None}), 200
    return jsonify({'success': True, 'product': product}), 200

from infrastructure.repositories.cart_repository import CartRepository
cart_repo = CartRepository()

@api_bp.route('/cart/add', methods=['POST'])
def add_to_cart():
    try:
        product = session.get('selected_product')
        if not product:
            return jsonify({'error': 'No product selected'}), 400
            
        data = request.get_json() or {}
        fit_status_text = data.get('fit_status_text')
        body_shape_text = data.get('body_shape_text')
        
        # Determine string values from text. DB now stores VARCHAR(50).
        fit_status = fit_status_text if fit_status_text else None
        body_shape = body_shape_text if body_shape_text else None
        
        # generate a simple session ID for the cart
        session_id = session.get('_id')
        if not session_id:
            import uuid
            session_id = str(uuid.uuid4())
            session['_id'] = session_id
            
        cart_repo.add_to_cart(
            session_id=session_id,
            product_id=product['id'],
            fit_status=fit_status,
            body_shape=body_shape
        )
        return jsonify({'success': True, 'message': 'Added to cart'}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/cart', methods=['GET'])
def get_cart():
    try:
        session_id = session.get('_id')
        if not session_id:
            return jsonify({'success': True, 'items': []}), 200
            
        cart_items = cart_repo.get_cart_by_session(session_id)
        items_data = []
        for item in cart_items:
            product = item.product
            items_data.append({
                "id_cart": item.id_cart,
                "fit_status": item.fit_status,
                "body_shape": item.body_shape,
                "product": {
                    "id": product.id_product,
                    "name": product.nama_produk,
                    "price": float(product.harga),
                    "image_url": product.gambar_url,
                    "category": "Clothes" # Defaulting for now
                }
            })
        return jsonify({'success': True, 'items': items_data}), 200
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@api_bp.route('/cart/<int:id_cart>', methods=['DELETE'])
def delete_cart_item(id_cart):
    try:
        success = cart_repo.remove_from_cart(id_cart)
        if success:
            return jsonify({'success': True, 'message': 'Item deleted'}), 200
        return jsonify({'error': 'Item not found'}), 404
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

# ============ ANALYSIS ENDPOINTS ============

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
        # Detect pose
        result = pose_service.pose_detector.detect(img)
        landmarks = pose_service.pose_detector.get_landmarks(result)
        
        if landmarks is None:
            return jsonify({
                'success': True,
                'aligned': False,
                'message': 'No pose detected'
            }), 200
            
        # Check if shoulders and hips are visible
        shoulders_hips = pose_service.pose_detector.are_shoulders_hips_visible(landmarks)
        
        if not shoulders_hips:
            return jsonify({
                'success': True,
                'aligned': False,
                'message': 'Shoulders and hips must be visible'
            }), 200
            
        cal_type = data.get('calibration_type', 'height')
        
        if cal_type == 'height':
            def is_visible(idx):
                try:
                    lm = landmarks[idx]
                    return 0 <= lm.x <= 1 and 0 <= lm.y <= 1
                except:
                    return False
            if not is_visible(0) or not (is_visible(27) or is_visible(28)):
                return jsonify({
                    'success': True,
                    'aligned': False,
                    'message': 'Entire body (head to toe) must be visible'
                }), 200
                
        elif cal_type == 'reference_auto':
            cal_value = float(data.get('calibration_value_cm', 8.56))
            scale = pose_service.reference_calibrator.calibrate(img, cal_value, landmarks)
            if scale is None:
                return jsonify({
                    'success': True,
                    'aligned': False,
                    'message': 'Card not detected. Hold it visibly in the frame.'
                }), 200
            
        return jsonify({
            'success': True,
            'aligned': True,
            'message': 'Pose aligned perfectly'
        }), 200
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500

@api_bp.route('/analyze', methods=['POST'])
def analyze():
    """Analyze image and return measurements based on session product"""
    try:
        product = session.get('selected_product')
        if not product:
            return jsonify({'error': 'Please select a product first'}), 400
            
        dress_size = product['target_dress_size_cm']
        
        # Handle Base64 (from WebRTC) or Multipart File (Upload)
        if request.is_json:
            data = request.get_json()
            image_b64 = data.get('image')
            if not image_b64:
                return jsonify({'error': 'No image provided in JSON'}), 400
                
            if ',' in image_b64:
                image_b64 = image_b64.split(',')[1]
            image_bytes = base64.b64decode(image_b64)
            
            cal_type_str = data.get('calibration_type', 'height')
            cal_value = float(data.get('calibration_value_cm', 0))
            user_height = float(data.get('user_height_cm', 165))
            ref_px = data.get('reference_pixel_length')
            ref_px = float(ref_px) if ref_px else None
            
        else:
            if 'image' not in request.files:
                return jsonify({'error': 'No image file provided'}), 400
            
            file = request.files['image']
            if file.filename == '':
                return jsonify({'error': 'Empty filename'}), 400
            
            image_bytes = file.read()
            
            cal_type_str = request.form.get('calibration_type', 'height')
            cal_value = float(request.form.get('calibration_value_cm', 0))
            user_height = float(request.form.get('user_height_cm', 165))
            ref_px_str = request.form.get('reference_pixel_length')
            ref_px = float(ref_px_str) if ref_px_str else None
        
        try:
            cal_type = CalibrationType(cal_type_str)
        except ValueError:
            return jsonify({'error': 'calibration_type must be "height" or "reference"'}), 400
        
        if cal_value <= 0:
            return jsonify({'error': 'calibration_value_cm must be positive'}), 400
            
        analysis_request = PoseAnalysisRequest(
            image_bytes=image_bytes,
            calibration_type=cal_type,
            calibration_value_cm=cal_value,
            user_height_cm=user_height,
            dress_size_cm=dress_size,
            reference_pixel_length=ref_px
        )
        
        is_valid, error_msg = analysis_request.validate()
        if not is_valid:
            return jsonify({'error': error_msg}), 400
        
        measurements, error = pose_service.analyze(analysis_request)
        
        if error:
            return jsonify({'error': error}), 400
        
        return jsonify({
            'success': True,
            'measurements': measurements.to_dict(),
            'calibration_method': cal_type.value,
            'product_target_size': dress_size
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({'error': f'Internal error: {str(e)}'}), 500

@api_bp.route('/health', methods=['GET'])
def health():
    return jsonify({'status': 'healthy', 'service': 'virtual-tailor'}), 200

# Cleanup
def cleanup():
    pose_service.close()