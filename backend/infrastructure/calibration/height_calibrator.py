import numpy as np
from typing import Optional, Any

class HeightCalibrator:
    # ADJUSTED RATIO: 0.88 (Kompensasi deteksi mata kaki pada pakaian/sepatu)
    HEAD_TO_ANKLE_RATIO: float = 0.88

    SCALE_MIN: float = 0.02
    SCALE_MAX: float = 1.5

    def calibrate(self, landmarks, image_width, image_height, user_height_cm):
        if not landmarks or len(landmarks) < 33 or user_height_cm <= 0:
            return None

        # Landmark 0 (Hidung) adalah jangkar paling stabil untuk sistem Anda
        nose = landmarks[0]
        left_ankle = landmarks[27]
        right_ankle = landmarks[28]

        # Gunakan mata kaki yang paling rendah untuk akurasi lantai
        ankle_y = max(left_ankle.y, right_ankle.y)
        height_px = abs(ankle_y - nose.y) * image_height

        if height_px < 50: return None

        # HITUNG SKALA
        effective_height_cm = user_height_cm * self.HEAD_TO_ANKLE_RATIO
        scale = effective_height_cm / height_px
        
        return float(scale)