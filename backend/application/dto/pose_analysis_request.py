from dataclasses import dataclass
from typing import Optional, Tuple
from enum import Enum

class CalibrationType(str, Enum):
    HEIGHT = "height"
    REFERENCE = "reference"
    REFERENCE_AUTO = "reference_auto"

@dataclass
class PoseAnalysisRequest:
    image_bytes: bytes
    calibration_type: CalibrationType
    calibration_value_cm: float
    user_height_cm: float = 165.0
    dress_size_cm: float = 110.0
    reference_pixel_length: Optional[float] = None
    
    def validate(self) -> Tuple[bool, Optional[str]]:
        if self.calibration_type == CalibrationType.HEIGHT:
            if not (100 <= self.calibration_value_cm <= 250):
                return False, "Height must be between 100-250 cm"
        elif self.calibration_type == CalibrationType.REFERENCE:
            if self.calibration_value_cm <= 0:
                return False, "Reference object size must be > 0 cm"
            if not self.reference_pixel_length or self.reference_pixel_length <= 0:
                return False, "Reference pixel length must be > 0"
        elif self.calibration_type == CalibrationType.REFERENCE_AUTO:
            if self.calibration_value_cm <= 0:
                return False, "Reference object size must be > 0 cm"
        
        if not (140 <= self.user_height_cm <= 200):
            return False, "User height must be between 140-200 cm"
        
        return True, None