from infrastructure.models.db_models import Cart
from extensions import db

class CartRepository:
    def add_to_cart(self, session_id: str, product_id: int, fit_status: str = None, body_shape: str = None):
        new_cart_item = Cart(
            session_id=session_id,
            id_product=product_id,
            fit_status=fit_status,
            body_shape=body_shape
        )
        db.session.add(new_cart_item)
        db.session.commit()
        return new_cart_item

    def get_cart_by_session(self, session_id: str):
        return Cart.query.filter_by(session_id=session_id).all()
        
    def remove_from_cart(self, id_cart: int):
        item = Cart.query.get(id_cart)
        if item:
            db.session.delete(item)
            db.session.commit()
            return True
        return False
