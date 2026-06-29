import re # Tambahkan import re untuk validasi format
from typing import Optional, Tuple
from werkzeug.security import generate_password_hash, check_password_hash
from infrastructure.repositories.user_repository import UserRepository
from infrastructure.models.db_models import User

class AuthService:
    def __init__(self):
        self.user_repo = UserRepository()

    def register(self, username: str, email: str, password: str, phone: Optional[str] = None) -> Tuple[Optional[User], Optional[str]]:
        # --- TAHAP VALIDASI KETAT ---

        # 1. Validasi Panjang Password (MINIMAL 6 KARAKTER)
        if not password or len(password) < 6:
            return None, "Kata sandi terlalu pendek! Minimal harus 6 karakter."

        # 2. Validasi Format Email menggunakan Regex
        email_pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
        if not re.match(email_pattern, email):
            return None, "Format email tidak valid (contoh: nama@mail.com)."

        # 3. Validasi Username (Minimal 3 karakter, tanpa spasi)
        if not username or len(username) < 3:
            return None, "Nama pelanggan minimal harus 3 karakter."
        if " " in username:
            return None, "Nama pelanggan tidak boleh mengandung spasi."

        # 4. Validasi duplikasi (Cek apakah email sudah terpakai)
        if self.user_repo.get_by_email(email):
            return None, "Email sudah terdaftar. Gunakan email lain."
            
        # 5. Validasi duplikasi (Cek apakah nomor HP sudah terpakai jika diisi)
        if phone and self.user_repo.get_by_phone(phone):
            return None, "Nomor handphone sudah terdaftar."

        # --- TAHAP PENYIMPANAN ---
        
        # Hash Password menggunakan standar pbkdf2:sha256
        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        
        new_user = User(
            username=username.strip(),
            email=email.lower().strip(),
            phone=phone.strip() if phone else None,
            password=hashed_password,
            role=0 # Default role user biasa
        )
        
        try:
            saved_user = self.user_repo.save(new_user)
            return saved_user, None
        except Exception as e:
            # Mengembalikan pesan error asli database jika terjadi kegagalan sistem
            return None, f"Gagal menyimpan data ke sistem: {str(e)}"

    def verify_login(self, email: str, password: str) -> Tuple[Optional[User], Optional[str]]:
        # Ambil user berdasarkan email
        user = self.user_repo.get_by_email(email)
        
        # Jika user tidak ada atau login via google (tidak punya password manual)
        if not user or not user.password:
            return None, "Email atau kata sandi Anda salah."
            
        # Cek kecocokan password manual dengan hash di database
        if check_password_hash(user.password, password):
            return user, None
            
        return None, "Email atau kata sandi Anda salah."

    def handle_google_login(self, email: str, username: str, google_id: str) -> Tuple[Optional[User], Optional[str]]:
        user = self.user_repo.get_by_email(email)
        
        if user:
            # Jika user sudah terdaftar secara manual, hubungkan dengan Google ID jika belum ada
            if not user.google_id:
                user.google_id = google_id
                self.user_repo.save(user)
            return user, None
        else:
            # Jika belum terdaftar, buat akun baru secara otomatis melalui Google
            new_user = User(
                username=username,
                email=email,
                google_id=google_id,
                role=0
            )
            saved_user = self.user_repo.save(new_user)
            return saved_user, None