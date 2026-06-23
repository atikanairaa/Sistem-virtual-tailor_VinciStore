from extensions import db

class User(db.Model):
    __tablename__ = 'users'
    id_user = db.Column(db.Integer, primary_key=True, autoincrement=True)
    username = db.Column(db.String(20), nullable=False)
    password = db.Column(db.String(6), nullable=False)
    role = db.Column(db.Boolean, nullable=False)

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
    session_id = db.Column(db.String(255), nullable=False)
    id_product = db.Column(db.Integer, db.ForeignKey('products.id_product', ondelete='CASCADE', onupdate='CASCADE'), nullable=False)
    fit_status = db.Column(db.String(50), nullable=True)
    body_shape = db.Column(db.String(50), nullable=True)

    product = db.relationship('Product', backref=db.backref('carts', lazy=True))
