from dataclasses import dataclass
from typing import Optional
import re

@dataclass
class User:
    id_user: Optional[int] = None
    username: Optional[str] = None
    email: Optional[str] = None
    phone: Optional[str] = None
    password: Optional[str] = None
    role: int = 0  # 0 untuk User, 1 untuk Admin
    google_id: Optional[str] = None
    
    def to_dict(self) -> dict:
        """
        Konversi objek ke dictionary.
        SANGAT PENTING: Atribut 'password' dan 'google_id' sengaja DIBUANG 
        agar tidak ikut terkirim sebagai JSON ke frontend/API response (Keamanan).
        """
        return {
            "id_user": self.id_user,
            "username": self.username,
            "email": self.email,
            "phone": self.phone,
            "role": self.role,
        }
    
    def is_valid(self) -> tuple[bool, str]:
        """
        Sanity-check format data User sebelum masuk ke database.
        Mengembalikan tuple: (Boolean Valid/Tidak, "Pesan Error").
        """
        # 1. Username harus ada dan panjangnya rasional
        if not self.username or len(self.username) < 3:
            return False, "Username harus memiliki minimal 3 karakter."
            
        # 2. Harus memiliki minimal salah satu: Email, Phone, atau Google ID
        if not self.email and not self.phone and not self.google_id:
            return False, "Minimal harus ada Email, Nomor HP, atau Google Login."
            
        # 3. Validasi format Email (jika ada)
        if self.email:
            email_regex = r'^[\w\.-]+@[\w\.-]+\.\w+$'
            if not re.match(email_regex, self.email):
                return False, "Format email tidak valid."
        
        # 4. Validasi Role (hanya 0 atau 1)
        if self.role not in (0, 1):
            return False, "Role tidak valid."
            
        return True, "Valid"