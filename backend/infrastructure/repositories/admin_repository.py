from infrastructure.models.db_models import UserHistory, Cart, Product
from extensions import db
from sqlalchemy import func
from datetime import datetime, timedelta

class AdminRepository:
    def get_conversion_stats(self):
        # 1. Hitung Unique Users (Logika agar Persentase tidak meledak > 100%)
        total_users_scanned = db.session.query(func.count(func.distinct(UserHistory.id_user))).scalar() or 0
        users_who_ordered = db.session.query(func.count(func.distinct(Cart.id_user)))\
                              .filter(Cart.status == 'ordered').scalar() or 0
        
        # 2. Total Angka untuk Card Dashboard
        total_scans = db.session.query(UserHistory).count()
        total_in_cart = db.session.query(Cart).filter(Cart.status == 'active').count()
        # FIX: Samakan key 'total_ordered' agar sinkron dengan JS valOrdered
        total_ordered = db.session.query(Cart).filter(Cart.status == 'ordered').count()

        # 3. Persentase Konversi Berbasis User
        conv_rate = round((users_who_ordered / total_users_scanned * 100), 1) if total_users_scanned > 0 else 0
        
        return {
            "total_scans": total_scans,
            "total_in_cart": total_in_cart,
            "total_ordered": total_ordered, # Key sudah sinkron dengan frontend
            "conversion_rate": conv_rate
        }

    def get_daily_trends(self):
        today = datetime.now().date()
        results = []
        for i in range(6, -1, -1):
            d = today - timedelta(days=i)
            # Hitung Scan
            scans = db.session.query(UserHistory).filter(func.date(UserHistory.created_at) == d).count()
            # Hitung Carts (Barang masuk keranjang di hari tsb)
            carts = db.session.query(Cart).filter(Cart.status == 'active', func.date(Cart.created_at) == d).count()
            # Hitung Orders (Barang dikonversi ke WA/Shopee di hari tsb)
            orders = db.session.query(Cart).filter(Cart.status == 'ordered', func.date(Cart.updated_at) == d).count()
            
            results.append({
                "date": d.strftime('%d %b'),
                "scans": scans,
                "carts": carts,
                "orders": orders
            })
        return results

    def get_product_activity(self):
        """Data Tabel: Nama Produk | Interaksi AI | Masuk Keranjang"""
        # Subquery Hitung Scan
        scan_sub = db.session.query(UserHistory.id_product, func.count(UserHistory.id_history).label('scans'))\
                     .group_by(UserHistory.id_product).subquery()
        
        # Subquery Hitung Keranjang Active
        cart_sub = db.session.query(Cart.id_product, func.count(Cart.id_cart).label('carts'))\
                     .filter(Cart.status == 'active').group_by(Cart.id_product).subquery()

        # Join Utama dengan Tabel Product
        query = db.session.query(
            Product.nama_produk, Product.gambar_url,
            func.coalesce(scan_sub.c.scans, 0),
            func.coalesce(cart_sub.c.carts, 0)
        ).outerjoin(scan_sub, Product.id_product == scan_sub.c.id_product)\
         .outerjoin(cart_sub, Product.id_product == cart_sub.c.id_product).all()
        
        return [{"name": q[0], "img": q[1], "scans": q[2], "carts": q[3]} for q in query]