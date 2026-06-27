from infrastructure.models.db_models import Cart
from extensions import db

class CartRepository:
    def add_to_cart(self, id_user, id_product, fit_status=None, body_shape=None):
        # Cek apakah barang sudah ada di keranjang
        existing = Cart.query.filter_by(id_user=id_user, id_product=id_product).first()
        
        if existing:
            # Jika barang sudah ada, TIMPA hasil AI lama dengan hasil AI yang baru
            existing.fit_status = fit_status
            existing.body_shape = body_shape
            db.session.commit()
            return existing
        
        # Jika barang belum ada, buat baru
        new_item = Cart(
            id_user=id_user, 
            id_product=id_product, 
            fit_status=fit_status, 
            body_shape=body_shape
        )
        db.session.add(new_item)
        db.session.commit()
        return new_item

    def get_user_cart(self, id_user):
        return Cart.query.filter_by(id_user=id_user).all()
    
    def soft_delete(self, id_cart, id_user):
        """Ubah status jadi removed daripada menghapus barisnya"""
        item = Cart.query.filter_by(id_cart=id_cart, id_user=id_user).first()
        if item:
            item.status = 'removed'
            db.session.commit()
            return True
        return False

    def mark_as_ordered(self, id_user):
        """Tandai barang sebagai 'ordered' saat user klik WA/Shopee"""
        items = Cart.query.filter_by(id_user=id_user, status='active').all()
        for item in items:
            item.status = 'ordered'
        db.session.commit()