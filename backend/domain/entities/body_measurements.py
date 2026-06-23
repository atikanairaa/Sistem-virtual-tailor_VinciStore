from dataclasses import dataclass
from typing import Optional
from domain.value_objects.body_shape import BodyShape
from domain.value_objects.fit_type import FitType

@dataclass
class BodyMeasurements:
    shoulder_width_cm: Optional[float] = None
    hip_width_cm: Optional[float] = None
    chest_width_cm: Optional[float] = None
    chest_circumference_cm: Optional[float] = None
    body_shape: Optional[BodyShape] = None
    fit_recommendation: Optional[FitType] = None
    
    def to_dict(self) -> dict:
        return {
            "shoulder_width_cm": round(self.shoulder_width_cm, 1) if self.shoulder_width_cm else None,
            "hip_width_cm": round(self.hip_width_cm, 1) if self.hip_width_cm else None,
            "chest_width_cm": round(self.chest_width_cm, 1) if self.chest_width_cm else None,
            "chest_circumference_cm": round(self.chest_circumference_cm, 1) if self.chest_circumference_cm else None,
            "body_shape": str(self.body_shape) if self.body_shape else None,
            "fit_recommendation": str(self.fit_recommendation) if self.fit_recommendation else None,
        }
    
    def is_valid(self) -> bool:
        """
        Sanity-check measurements are within human physiological ranges.
        Ranges are intentionally wide to accommodate diverse body types
        and varying camera distances.
        """
        if self.shoulder_width_cm and not (15 <= self.shoulder_width_cm <= 100):
            print(f"[BodyMeasurements] !! Shoulder out of range: {self.shoulder_width_cm:.1f}cm (expected 15-100)")
            return False
        if self.chest_circumference_cm and not (45 <= self.chest_circumference_cm <= 200):
            print(f"[BodyMeasurements] !! Chest circ out of range: {self.chest_circumference_cm:.1f}cm (expected 45-200)")
            return False
        return True