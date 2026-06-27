from extensions import db
from flask_login import UserMixin

class User(db.Model, UserMixin):
    __tablename__ = 'users'
    id_user = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(50), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=True)
    phone = db.Column(db.String(20), unique=True, nullable=True)
    password = db.Column(db.String(255), nullable=True)
    google_id = db.Column(db.String(100), unique=True, nullable=True)
    role = db.Column(db.Integer, nullable=False, default=0)

    def get_id(self):
        return str(self.id_user)
    
class Product(db.Model):
    __tablename__ = 'products'
    id_product = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id_user', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    nama_produk = db.Column(db.String(255), nullable=False)
    deskripsi = db.Column(db.Text, nullable=False)
    harga = db.Column(db.Numeric(10, 2), nullable=False)
    gambar_url = db.Column(db.String(255), nullable=False)

    user = db.relationship('User', backref=db.backref('products', lazy=True))

class SizeChart(db.Model):
    __tablename__ = 'size_charts'
    id_size = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_produk = db.Column(db.Integer, db.ForeignKey('products.id_product', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    ld_produk = db.Column(db.Float, nullable=False)
    panjang_produk = db.Column(db.Float, nullable=False)

    product = db.relationship('Product', backref=db.backref('size_charts', lazy=True))

class Cart(db.Model):
    __tablename__ = 'carts'
    id_cart = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id_user', ondelete='CASCADE'), nullable=False)
    id_product = db.Column(db.Integer, db.ForeignKey('products.id_product', ondelete='CASCADE'), nullable=False)
    status = db.Column(db.Enum('active', 'removed', 'ordered'), default='active', nullable=False)
    fit_status = db.Column(db.String(50), nullable=True)
    body_shape = db.Column(db.String(50), nullable=True)
    
    # --- FIX: TAMBAHKAN KOLOM WAKTU DI SINI ---
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    product = db.relationship('Product', backref=db.backref('carts', lazy=True))
    user = db.relationship('User', backref=db.backref('user_carts', lazy=True))

class UserHistory(db.Model):
    __tablename__ = 'user_history'
    id_history = db.Column(db.Integer, primary_key=True, autoincrement=True)
    id_user = db.Column(db.Integer, db.ForeignKey('users.id_user', ondelete='CASCADE'), nullable=False)
    id_product = db.Column(db.Integer, db.ForeignKey('products.id_product', ondelete='CASCADE'), nullable=False)
    fit_status = db.Column(db.String(50))
    body_shape = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())

    product = db.relationship('Product')
    user = db.relationship('User')