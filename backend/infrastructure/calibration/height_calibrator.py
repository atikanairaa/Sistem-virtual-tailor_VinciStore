import numpy as np
from typing import Optional, Any


class HeightCalibrator:
    """
    Calibrate pixel-to-cm scale using known user height.
    
    Strategy:
    - Use vertical y-coordinate difference (head top -> ankle) converted to pixels.
    - The head-to-ankle span covers ~88% of total body height.
    - We widen the acceptable scale range to handle both close-up and far-away shots.
    """

    # Head (nose tip, landmark 0) to ankle covers ~88% of total standing height
    HEAD_TO_ANKLE_RATIO: float = 0.88

    # Acceptable scale range in cm/pixel:
    # - MIN: person very far away, body spans most of the frame
    # - MAX: person very close, only upper body barely fits in frame
    SCALE_MIN: float = 0.02
    SCALE_MAX: float = 1.5

    def calibrate(
        self,
        landmarks: Any,
        image_width: int,
        image_height: int,
        user_height_cm: float,
    ) -> Optional[float]:
        """
        Calculate scale (cm per pixel) from known user height.

        Args:
            landmarks: MediaPipe pose landmarks list (33 points).
            image_width:  Frame width in pixels.
            image_height: Frame height in pixels.
            user_height_cm: Real-world height of the user in cm.

        Returns:
            Scale value (cm/px) or None on failure.
        """
        if not landmarks or len(landmarks) <= 28 or user_height_cm <= 0:
            print(
                f"[HeightCalibrator] Invalid input: "
                f"landmarks={landmarks is not None}, "
                f"len={len(landmarks) if landmarks else 0}, "
                f"height={user_height_cm}"
            )
            return None

        head = landmarks[0]
        left_ankle = landmarks[27]
        right_ankle = landmarks[28]

        print(f"[HeightCalibrator] Head:        x={head.x:.3f}, y={head.y:.3f}")
        print(f"[HeightCalibrator] Left ankle:  x={left_ankle.x:.3f}, y={left_ankle.y:.3f}")
        print(f"[HeightCalibrator] Right ankle: x={right_ankle.x:.3f}, y={right_ankle.y:.3f}")

        # --- Visibility checks ---
        def is_visible(lm, y_min: float = 0.0, y_max: float = 1.05) -> bool:
            return 0.02 <= lm.x <= 0.98 and y_min <= lm.y <= y_max

        head_visible = is_visible(head, y_min=0.0, y_max=0.50)
        left_visible = is_visible(left_ankle, y_min=0.50, y_max=1.05)
        right_visible = is_visible(right_ankle, y_min=0.50, y_max=1.05)

        print(
            f"[HeightCalibrator] Visibility: "
            f"Head={head_visible}, "
            f"Left ankle={left_visible}, "
            f"Right ankle={right_visible}"
        )

        if not head_visible or not (left_visible or right_visible):
            print("[HeightCalibrator] Body not fully visible (head or ankles out of frame)")
            return None

        # Prefer the ankle that is more visible (closer to y=0.75 centroid)
        ankle = left_ankle if left_visible else right_ankle
        if left_visible and right_visible:
            # Use average y of both ankles for better accuracy
            avg_ankle_y = (left_ankle.y + right_ankle.y) / 2.0
            # Synthetic "average ankle" for pixel calculation
            class _AvgAnkle:
                x = (left_ankle.x + right_ankle.x) / 2.0
                y = avg_ankle_y
            ankle = _AvgAnkle()

        # --- Pixel height: use VERTICAL component only ---
        # Using only dy avoids inflating the pixel distance with horizontal sway.
        delta_y_norm = ankle.y - head.y          # normalised (0-1)
        height_px = abs(delta_y_norm) * image_height

        print(f"[HeightCalibrator] Vertical span: {delta_y_norm:.4f} -> {height_px:.1f} px")

        if height_px < 30:
            print(f"[HeightCalibrator] Height too small: {height_px:.1f}px (min 30px) - stand further from camera")
            return None

        # --- Scale calculation ---
        effective_height_cm = user_height_cm * self.HEAD_TO_ANKLE_RATIO
        scale = effective_height_cm / height_px

        print(
            f"[HeightCalibrator] Effective height: {effective_height_cm:.1f}cm / "
            f"{height_px:.1f}px -> scale = {scale:.6f} cm/px"
        )

        if self.SCALE_MIN <= scale <= self.SCALE_MAX:
            print(f"[HeightCalibrator] OK Scale accepted: {scale:.6f} cm/px")
            return float(scale)

        print(
            f"[HeightCalibrator] !! Scale out of range: {scale:.6f} "
            f"(expected {self.SCALE_MIN}--{self.SCALE_MAX})"
        )
        return None