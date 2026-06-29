from infrastructure.models.db_models import UserHistory, Cart, Product
from extensions import db
from sqlalchemy import func
from datetime import datetime, timedelta

class AdminRepository:
    def get_conversion_stats(self):
        # 1. Total User Unik yang melakukan Scan AI (User Adoption)
        unique_users = db.session.query(func.count(func.distinct(UserHistory.id_user))).scalar() or 0
        
        # 2. Total Kumulatif Scan AI yang dilakukan (AI Usage)
        total_scans = db.session.query(UserHistory).count()
        
        # 3. Total Produk yang masuk ke Keranjang (Product Interest)
        total_in_cart = db.session.query(Cart).count()

        # Metrik Tambahan: Rata-rata scan per user (Opsional untuk dashboard)
        avg_scan = round(total_scans / unique_users, 1) if unique_users > 0 else 0
        
        return {
            "unique_users_ai": unique_users,
            "total_scans": total_scans,
            "total_in_cart": total_in_cart,
            "avg_scan_per_user": avg_scan
        }



    def get_product_activity(self):
        """Menghasilkan laporan per produk diurutkan berdasarkan interaksi AI terbanyak"""
        # Subquery Hitung Scan
        scan_sub = db.session.query(
            UserHistory.id_product, 
            func.count(UserHistory.id_history).label('scans')
        ).group_by(UserHistory.id_product).subquery()
        
        # Subquery Hitung Keranjang
        cart_sub = db.session.query(
            Cart.id_product, 
            func.count(Cart.id_cart).label('carts')
        ).filter(Cart.status == 'active').group_by(Cart.id_product).subquery()

        # Join dan Urutkan Berdasarkan Scans Terbanyak (DESC)
        query = db.session.query(
            Product.nama_produk, 
            Product.gambar_url,
            func.coalesce(scan_sub.c.scans, 0).label('total_scans'),
            func.coalesce(cart_sub.c.carts, 0)
        ).outerjoin(scan_sub, Product.id_product == scan_sub.c.id_product)\
         .outerjoin(cart_sub, Product.id_product == cart_sub.c.id_product)\
         .order_by(func.coalesce(scan_sub.c.scans, 0).desc()).all() # FIX: SORTING DI SINI
        
        return [{"name": q[0], "img": q[1], "scans": q[2], "carts": q[3]} for q in query]

    def get_users_list(self):
        from infrastructure.models.db_models import User
        users = db.session.query(
            User.username,
            User.email,
            func.count(UserHistory.id_history).label('total_scans'),
            func.max(UserHistory.created_at).label('last_scan')
        ).join(UserHistory, User.id_user == UserHistory.id_user)\
         .filter(User.role == 0)\
         .group_by(User.id_user)\
         .having(func.count(UserHistory.id_history) > 0)\
         .order_by(func.count(UserHistory.id_history).desc()).all()
        
        return [{
            "username": u[0],
            "email": u[1] or '-',
            "scans": u[2],
            "last_scan": u[3].strftime('%d %b %Y %H:%M') if u[3] else '-'
        } for u in users]

    def get_scans_list(self):
        from infrastructure.models.db_models import User
        scans = db.session.query(
            User.username,
            Product.nama_produk,
            UserHistory.fit_status,
            UserHistory.body_shape,
            UserHistory.created_at
        ).join(User, UserHistory.id_user == User.id_user)\
         .join(Product, UserHistory.id_product == Product.id_product)\
         .order_by(UserHistory.created_at.desc()).all()

        return [{
            "username": s[0],
            "product": s[1],
            "fit": s[2],
            "shape": s[3],
            "date": s[4].strftime('%d %b %Y %H:%M') if s[4] else '-'
        } for s in scans]

    def get_carts_list(self):
        from infrastructure.models.db_models import User
        carts = db.session.query(
            User.username,
            Product.nama_produk,
            Cart.status,
            Cart.created_at
        ).join(User, Cart.id_user == User.id_user)\
         .join(Product, Cart.id_product == Product.id_product)\
         .order_by(Cart.created_at.desc()).all()

        return [{
            "username": c[0],
            "product": c[1],
            "status": c[2],
            "date": c[3].strftime('%d %b %Y %H:%M') if c[3] else '-'
        } for c in carts]