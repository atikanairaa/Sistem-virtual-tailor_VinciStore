from infrastructure.models.db_models import Product, SizeChart
from extensions import db

class ProductRepository:
    def get_active_products(self):
        """Digunakan untuk KATALOG USER (index.html)"""
        return db.session.query(Product).filter(Product.status == 'active').all()

    def get_all_products_admin(self):
        """Digunakan untuk DASHBOARD ADMIN"""
        return db.session.query(Product).all()

    def get_product_by_id(self, product_id):
        return db.session.query(Product).filter(Product.id_product == product_id).first()

    def archive_product(self, product_id):
        """Hanya menyembunyikan dari katalog, data histori tetap aman"""
        product = self.get_product_by_id(product_id)
        if product:
            product.status = 'archived'
            db.session.commit()
            return True
        return False

    def save_product(self, product: Product, ld, panjang):
        db.session.add(product)
        db.session.flush() 
        sc = SizeChart(id_produk=product.id_product, ld_produk=ld, panjang_produk=panjang)
        db.session.add(sc)
        db.session.commit()
        return product

    def update_product(self, product_id, data, ld, panjang):
        product = self.get_product_by_id(product_id)
        if product:
            product.nama_produk = data['name']
            product.deskripsi = data['description']
            product.harga = data['price']
            product.gambar_url = data['image_url']
            
            # Update SizeChart
            if product.size_charts:
                sc = product.size_charts[0]
                sc.ld_produk = ld
                sc.panjang_produk = panjang
            
            db.session.commit()
            return True
        return False

    def delete_product(self, product_id):
        product = self.get_product_by_id(product_id)
        if product:
            db.session.delete(product)
            db.session.commit()
            return True
        return False