import cv2
import numpy as np
from typing import Optional, Any

class ReferenceCalibrator:
    """
    Calibrate pixel-to-cm scale using a standard reference object (e.g., ID Card, ATM Card).
    
    Strategy:
    - Standard ID-1 card dimensions are 85.60 mm x 53.98 mm.
    - Expected aspect ratio (width / height) is approx 1.586.
    - Use OpenCV contour detection to find the card in the image.
    - Calculate scale by mapping the physical width to the detected pixel width.
    """
    
    # Standard width of ATM/ID card in cm
    STANDARD_CARD_WIDTH_CM: float = 8.56
    
    # Expected aspect ratio (w/h)
    EXPECTED_ASPECT_RATIO: float = 1.586
    ASPECT_RATIO_TOLERANCE: float = 0.35 # Relaxed to allow for fingers covering corners
    
    # Acceptable scale ranges (cm/px) to prevent absurd calibrations
    SCALE_MIN: float = 0.005
    SCALE_MAX: float = 2.0

    def calibrate(self, image: np.ndarray, real_width_cm: float = STANDARD_CARD_WIDTH_CM, landmarks: Any = None) -> Optional[float]:
        """
        Calculate scale (cm per pixel) from a detected reference card.

        Args:
            image: BGR numpy image array.
            real_width_cm: Expected real-world width of the reference object in cm.

        Returns:
            Scale value (cm/px) or None on failure.
        """
        if image is None or image.size == 0:
            print("[ReferenceCalibrator] Invalid image input.")
            return None
            
        print(f"[ReferenceCalibrator] Starting card detection for width: {real_width_cm}cm")

        # 1. Grayscale conversion
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # --- UI-Synchronized Static ROI Cropping ---
        # The frontend draws a static box for the card (w=30%, centered, y=44%).
        # We crop the image to slightly larger than that box (+5% margin) to account for hand shake.
        try:
            img_h, img_w = gray.shape
            card_w = img_w * 0.3
            card_h = card_w / 1.586
            card_x = (img_w - card_w) / 2
            card_y = img_h * 0.44
            
            margin_x = img_w * 0.05
            margin_y = img_h * 0.05
            
            roi_x1 = int(max(0, card_x - margin_x))
            roi_x2 = int(min(img_w, card_x + card_w + margin_x))
            roi_y1 = int(max(0, card_y - margin_y))
            roi_y2 = int(min(img_h, card_y + card_h + margin_y))
            
            gray = gray[roi_y1:roi_y2, roi_x1:roi_x2]
            print(f"[ReferenceCalibrator] Cropped UI ROI: x({roi_x1}-{roi_x2}), y({roi_y1}-{roi_y2})")
        except Exception as e:
            print(f"[ReferenceCalibrator] Failed to crop UI ROI: {e}")
        # --------------------------
        
        # 2. Pre-processing: CLAHE to handle shadows and glare locally
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
        gray = clahe.apply(gray)
        
        # Blur to reduce noise
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # 3. Edge detection
        # Auto-Canny based on image median brightness. Much cleaner than Adaptive Thresholding
        # which can create noise bridges connecting the card to the shirt.
        v = np.median(blurred)
        sigma = 0.33
        lower = int(max(0, (1.0 - sigma) * v))
        upper = int(min(255, (1.0 + sigma) * v))
        edged = cv2.Canny(blurred, lower, upper)
        
        # 4. Morphological Closing to close gaps caused by glare or weak edges
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        edged = cv2.morphologyEx(edged, cv2.MORPH_CLOSE, kernel, iterations=2)
        
        # 5. Find contours (Use RETR_LIST to find the card even if it's enclosed by a shirt contour)
        contours, _ = cv2.findContours(edged.copy(), cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
        
        # Sort contours by area, largest first, take top 20
        contours = sorted(contours, key=cv2.contourArea, reverse=True)[:20]
        
        card_contour = None
        for c in contours:
            area = cv2.contourArea(c)
            if area < 100:  # Ignore very small noise. Lowered to 100 to allow cards from further distances.
                continue
                
            # Get convex hull to fill in gaps from fingers holding the card
            hull = cv2.convexHull(c)
            hull_area = cv2.contourArea(hull)
            
            if hull_area == 0:
                continue
                
            # Calculate solidity. A card partially covered by fingers still has high solidity.
            solidity = float(area) / hull_area
            if solidity < 0.7:
                continue
                
            # Calculate minAreaRect of the convex hull
            rect = cv2.minAreaRect(hull)
            (center, (width, height), angle) = rect
            
            if width == 0 or height == 0:
                continue
                
            # Reject if the detected "card" is unrealistically large (e.g. it detected the torso boundary itself)
            # A standard card shouldn't take up more than ~35% of the full image width
            img_w_full = image.shape[1]
            if max(width, height) > img_w_full * 0.35:
                continue
                
            # Aspect ratio of the bounding rectangle
            aspect_ratio = max(width, height) / min(width, height)
            
            if abs(aspect_ratio - self.EXPECTED_ASPECT_RATIO) <= self.ASPECT_RATIO_TOLERANCE:
                card_contour = hull
                break
        
        if card_contour is None:
            print("[ReferenceCalibrator] No valid card contour found. Ensure good lighting and high contrast.")
            return None
            
        # 6. Calculate dimensions using minAreaRect to handle rotation
        rect = cv2.minAreaRect(card_contour)
        (center, (width, height), angle) = rect
        
        # We assume the longer side is the width of the card
        pixel_width = max(width, height)
        
        if pixel_width < 20:
            print(f"[ReferenceCalibrator] Detected card is too small in the image ({pixel_width:.1f}px).")
            return None
            
        # 7. Calculate scale (Only rely on width for highest accuracy)
        # Using area can artificially inflate scale if fingers cover the card.
        # Using width (minAreaRect) is much more robust as long as the edges are somewhat visible.
        
        # Scale from width (cm/px)
        scale = real_width_cm / pixel_width
        
        print(f"[ReferenceCalibrator] Card found! Pixel width: {pixel_width:.1f}px")
        print(f"[ReferenceCalibrator] Final Scale: {scale:.6f} cm/px")
        
        # 8. Sanity check
        if self.SCALE_MIN <= scale <= self.SCALE_MAX:
            print(f"[ReferenceCalibrator] OK Scale accepted: {scale:.6f} cm/px")
            return float(scale)
            
        print(f"[ReferenceCalibrator] !! Scale out of range: {scale:.6f} (expected {self.SCALE_MIN}--{self.SCALE_MAX})")
        return None
