from flask import Blueprint, jsonify, request
from flask_login import login_required, current_user
from infrastructure.security.decorators import admin_required
from infrastructure.repositories.product_repository import ProductRepository
from infrastructure.repositories.admin_repository import AdminRepository
from infrastructure.models.db_models import Product

admin_bp = Blueprint('admin', __name__, url_prefix='/api/v1/admin')

# Inisialisasi Repository secara dinamis (Thread-Safe)
def get_repos():
    return ProductRepository(), AdminRepository()

# ============ STATS & REPORTING ============

@admin_bp.route('/stats', methods=['GET'])
@login_required
@admin_required
def get_stats():
    _, admin_repo = get_repos()
    return jsonify({
        "summary": admin_repo.get_conversion_stats(),
        "trends": admin_repo.get_daily_trends(),
        "activity": admin_repo.get_product_activity()
    })

# ============ PRODUCT CRUD ============

@admin_bp.route('/products/add', methods=['POST'])
@login_required
@admin_required
def add_product():
    product_repo, _ = get_repos()
    data = request.get_json()
    
    try:
        new_p = Product(
            id_user=current_user.id_user, # ID Admin otomatis
            nama_produk=data['name'],
            deskripsi=data['description'],
            harga=data['price'],
            gambar_url=data['image_url']
        )
        
        product_repo.save_product(
            new_p, 
            ld=data['ld'], 
            panjang=data['panjang']
        )
        
        return jsonify({"success": True, "message": "Produk berhasil ditambahkan"}), 201
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/products/update/<int:id>', methods=['PUT'])
@login_required
@admin_required
def update_product(id):
    product_repo, _ = get_repos()
    data = request.get_json()
    
    try:
        # Panggil fungsi update di repository
        success = product_repo.update_product(
            product_id=id,
            data=data,
            ld=data['ld'],
            panjang=data['panjang']
        )
        
        if success:
            return jsonify({"success": True, "message": "Produk berhasil diperbarui"})
        return jsonify({"success": False, "message": "Produk tidak ditemukan"}), 404
        
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500

@admin_bp.route('/products/delete/<int:id>', methods=['DELETE'])
@login_required
@admin_required
def delete_product(id):
    product_repo, _ = get_repos()
    try:
        success = product_repo.delete_product(id)
        if success:
            return jsonify({"success": True, "message": "Produk berhasil dihapus"})
        return jsonify({"success": False, "message": "Produk tidak ditemukan"}), 404
    except Exception as e:
        return jsonify({"success": False, "message": str(e)}), 500