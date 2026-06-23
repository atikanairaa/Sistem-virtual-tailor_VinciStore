from infrastructure.models.db_models import Product

class ProductRepository:
    def get_all_products(self):
        return Product.query.all()

    def get_product_by_id(self, product_id: int):
        return Product.query.get(product_id)
