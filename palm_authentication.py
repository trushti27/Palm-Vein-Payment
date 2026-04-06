"""
palm_authentication.py
----------------------
Simulates palm vein biometric authentication using:
  - OpenCV for image processing
  - ORB (Oriented FAST and Rotated BRIEF) for feature extraction
  - BFMatcher (Brute-Force Matcher) for descriptor matching

Authentication succeeds when the number of "good" feature matches
between the stored palm image and the input palm image meets or
exceeds MATCH_THRESHOLD.
"""

import cv2
import numpy as np
import os


# ──────────────────────────────────────────────
# CONFIGURATION
# ──────────────────────────────────────────────

IMAGE_SIZE = (256, 256)          # All images are resized to this before processing
MATCH_THRESHOLD = 15             # Minimum number of good matches required to authenticate
GOOD_MATCH_RATIO = 0.75          # Lowe's ratio test: keep matches where dist < ratio * second_dist
ORB_FEATURES = 500               # Maximum number of ORB keypoints to detect


# ──────────────────────────────────────────────
# IMAGE PREPROCESSING
# ──────────────────────────────────────────────

def preprocess_image(image_path: str) -> np.ndarray | None:
    """
    Load an image from disk, convert to grayscale, and resize it.

    Steps:
        1. Read image file using OpenCV.
        2. Convert BGR colour image to grayscale.
        3. Resize to IMAGE_SIZE for consistent comparison.
        4. Apply CLAHE (histogram equalisation) to enhance vein contrast.

    Args:
        image_path: Absolute or relative path to the palm image file.

    Returns:
        Preprocessed grayscale numpy array, or None if loading failed.
    """
    if not os.path.exists(image_path):
        print(f"[AUTH] Error: Image not found → {image_path}")
        return None

    # Load image in colour first
    img = cv2.imread(image_path)
    if img is None:
        print(f"[AUTH] Error: Could not read image → {image_path}")
        return None

    # Convert to grayscale
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    # Resize to standard dimensions
    resized = cv2.resize(gray, IMAGE_SIZE, interpolation=cv2.INTER_AREA)

    # Apply CLAHE to enhance local contrast (simulates vein enhancement)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(resized)

    return enhanced


# ──────────────────────────────────────────────
# FEATURE EXTRACTION
# ──────────────────────────────────────────────

def extract_features(image: np.ndarray):
    """
    Detect ORB keypoints and compute descriptors for a preprocessed image.

    ORB is chosen because it is:
      - Fast and efficient (suitable for real-time simulation)
      - Free to use (unlike SIFT/SURF)
      - Robust to rotation and scale changes

    Args:
        image: Grayscale numpy array (already preprocessed).

    Returns:
        Tuple (keypoints, descriptors).
        Returns (None, None) if no features are found.
    """
    orb = cv2.ORB_create(nfeatures=ORB_FEATURES)
    keypoints, descriptors = orb.detectAndCompute(image, None)

    if descriptors is None or len(keypoints) == 0:
        print("[AUTH] Warning: No features detected in image.")
        return None, None

    return keypoints, descriptors


# ──────────────────────────────────────────────
# FEATURE MATCHING
# ──────────────────────────────────────────────

def match_features(desc1: np.ndarray, desc2: np.ndarray) -> int:
    """
    Match ORB descriptors from two images using BFMatcher + Lowe's ratio test.

    BFMatcher with Hamming distance is the correct choice for ORB binary
    descriptors. The ratio test filters out ambiguous matches where the
    best match is not clearly better than the second-best match.

    Args:
        desc1: Descriptors from the stored (registered) palm image.
        desc2: Descriptors from the input (test) palm image.

    Returns:
        Number of good matches that passed the ratio test.
    """
    # BFMatcher with Hamming distance (required for ORB binary descriptors)
    bf = cv2.BFMatcher(cv2.NORM_HAMMING, crossCheck=False)

    # knnMatch: find the 2 nearest neighbours for each descriptor
    try:
        matches = bf.knnMatch(desc1, desc2, k=2)
    except cv2.error as e:
        print(f"[AUTH] Matching error: {e}")
        return 0

    # Apply Lowe's ratio test to keep only reliable matches
    good_matches = []
    for match_pair in matches:
        if len(match_pair) == 2:
            m, n = match_pair
            if m.distance < GOOD_MATCH_RATIO * n.distance:
                good_matches.append(m)

    return len(good_matches)


# ──────────────────────────────────────────────
# MAIN AUTHENTICATION FUNCTION
# ──────────────────────────────────────────────

def authenticate_palm(stored_image_path: str, input_image_path: str) -> dict:
    """
    Authenticate a user by comparing their input palm image against
    their stored (registered) palm image.

    Workflow:
        1. Preprocess both images (grayscale, resize, CLAHE).
        2. Extract ORB features from both images.
        3. Match descriptors using BFMatcher + ratio test.
        4. Compare match count against MATCH_THRESHOLD.

    Args:
        stored_image_path: Path to the palm image saved during registration.
        input_image_path:  Path to the palm image provided at payment time.

    Returns:
        A result dictionary:
        {
            "authenticated": bool,
            "match_count":   int,
            "threshold":     int,
            "message":       str
        }
    """
    result = {
        "authenticated": False,
        "match_count": 0,
        "threshold": MATCH_THRESHOLD,
        "message": ""
    }

    # Step 1 – Preprocess images
    print("[AUTH] Preprocessing stored palm image...")
    stored_img = preprocess_image(stored_image_path)
    if stored_img is None:
        result["message"] = "Failed to load stored palm image."
        return result

    print("[AUTH] Preprocessing input palm image...")
    input_img = preprocess_image(input_image_path)
    if input_img is None:
        result["message"] = "Failed to load input palm image."
        return result

    # Step 2 – Extract features
    print("[AUTH] Extracting ORB features from stored image...")
    kp1, desc1 = extract_features(stored_img)

    print("[AUTH] Extracting ORB features from input image...")
    kp2, desc2 = extract_features(input_img)

    if desc1 is None or desc2 is None:
        result["message"] = "Feature extraction failed — insufficient keypoints."
        return result

    print(f"[AUTH] Keypoints detected → stored: {len(kp1)}, input: {len(kp2)}")

    # Step 3 – Match descriptors
    print("[AUTH] Matching features using BFMatcher...")
    good_matches = match_features(desc1, desc2)
    result["match_count"] = good_matches

    print(f"[AUTH] Good matches: {good_matches} / threshold: {MATCH_THRESHOLD}")

    # Step 4 – Decision
    if good_matches >= MATCH_THRESHOLD:
        result["authenticated"] = True
        result["message"] = (
            f"Authentication SUCCESSFUL — {good_matches} feature matches found "
            f"(threshold: {MATCH_THRESHOLD})."
        )
    else:
        result["authenticated"] = False
        result["message"] = (
            f"Authentication FAILED — only {good_matches} feature matches found "
            f"(threshold: {MATCH_THRESHOLD} required)."
        )

    return result


# ──────────────────────────────────────────────
# UTILITY: List available images in dataset folder
# ──────────────────────────────────────────────

def list_dataset_images(dataset_dir: str) -> list[str]:
    """
    Recursively find all image files (.jpg, .jpeg, .png, .bmp) inside
    the given dataset directory.

    Args:
        dataset_dir: Path to the dataset root folder.

    Returns:
        Sorted list of absolute image file paths.
    """
    #supported_ext = (".jpg", ".jpeg", ".png", ".bmp")
    supported_ext = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif")
    image_paths = []

    if not os.path.isdir(dataset_dir):
        print(f"[AUTH] Dataset directory not found: {dataset_dir}")
        return image_paths

    for root, _, files in os.walk(dataset_dir):
        for f in files:
            if f.lower().endswith(supported_ext):
                image_paths.append(os.path.join(root, f))

    return sorted(image_paths)