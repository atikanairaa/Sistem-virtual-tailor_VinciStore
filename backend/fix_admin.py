from app import create_app
from extensions import db
from infrastructure.models.db_models import User
from werkzeug.security import generate_password_hash

app = create_app()
with app.app_context():
    # Cari user ID 1
    admin = User.query.get(1)
    
    if admin:
        print(f"Mengupdate Admin: {admin.username}")
        # SET EMAIL & PASSWORD DI SINI
        admin.email = "admin@gmail.com" # Masukkan email ini saat login nanti
        admin.password = generate_password_hash("admin123", method='pbkdf2:sha256')
        admin.role = 1
        db.session.commit()
        print("✅ SUCCESS: Admin ID 1 telah direset.")
        print("👉 Login dengan Email: admin@gmail.com | Password: admin123")
    else:
        print("❌ ERROR: User ID 1 tidak ditemukan di database.")