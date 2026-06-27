from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

class CalibrationType(str, Enum):
    HEIGHT = "height"

@dataclass
class PoseAnalysisRequest:
    image_bytes: bytes
    calibration_type: CalibrationType
    calibration_value_cm: float
    user_height_cm: float
    dress_size_cm: float = 110.0
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        if self.calibration_type == CalibrationType.HEIGHT:
            if not (100 <= self.user_height_cm <= 250):
                return False, "Tinggi badan harus antara 100-250 cm"
            
            if not (100 <= self.calibration_value_cm <= 250):
                return False, "Nilai kalibrasi tidak valid"
        
        return True, None