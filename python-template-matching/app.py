import cv2
import numpy as np
import os
from datetime import datetime

# --- Checking if image is a proper color image ---
def is_color_image(image):
    if len(image.shape) < 3 or image.shape[2] != 3:
        return False
    b, g, r = cv2.split(image)
    return not (np.array_equal(b, g) and np.array_equal(b, r))

# --- Loading images from user ---
def load_images():
    image_path_1 = input("Enter path of original image: ").strip()
    image_path_2 = input("Enter path of template image: ").strip()

    original_color_img = cv2.imread(image_path_1)
    template_color_img = cv2.imread(image_path_2)

    if original_color_img is None or template_color_img is None:
        raise ValueError("One or both images could not be loaded. Check the file paths.")

    return original_color_img, template_color_img, os.path.basename(image_path_1)

# --- Performing template matching to find coordinates ---
def find_template_coordinates(original_img, template_img):
    result = cv2.matchTemplate(original_img, template_img, cv2.TM_CCOEFF_NORMED)
    min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(result)
    top_left = max_loc
    height, width = template_img.shape[:2]
    bottom_right = (top_left[0] + width, top_left[1] + height)
    return top_left, bottom_right, max_val

# --- Comparing cropped region with template to verify match ---
def compare_cropped_with_template(cropped_region, template_img, threshold=0.9):
    if cropped_region.shape != template_img.shape:
        # Resize template to match cropped region size if slightly off
        template_img = cv2.resize(template_img, (cropped_region.shape[1], cropped_region.shape[0]))
    
    result = cv2.matchTemplate(cropped_region, template_img, cv2.TM_CCOEFF_NORMED)
    _, max_val, _, _ = cv2.minMaxLoc(result)
    return max_val >= threshold, max_val

# --- Performing matching given coordinates and verify with cropped comparison ---
def match_template_with_coordinates(original_img, template_img, top_left, bottom_right, match_threshold=0.9, original_filename="image.png"):
    matched_region = original_img[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]

    if matched_region.size == 0:
        print("\nObject not detected: Cropped region is empty.")
        return

    # --- Compare cropped region with template ---
    is_verified, verification_score = compare_cropped_with_template(matched_region, template_img, threshold=match_threshold)

    if not is_verified:
        print(f"\nObject not detected: Cropped region did not match template. Verification score: {round(verification_score, 4)}")
        return

    # --- Draw rectangle and save result image ---
    detected_image = original_img.copy()
    cv2.rectangle(detected_image, top_left, bottom_right, (0, 255, 0), 2)

    output_dir = "template_matches"
    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = os.path.splitext(original_filename)[0]
    output_filename = os.path.join(output_dir, f"detected_{base_filename}_{timestamp}.png")

    cv2.imwrite(output_filename, detected_image)
    print(f"Object detected and saved as: {output_filename}")
    #print(f"Verification match score: {round(verification_score, 4)}")

# --- Full combined function ---
def perform_full_template_matching():
    original_color_img, template_color_img, original_filename = load_images()

    # Check color types
    original_is_color = is_color_image(original_color_img)
    template_is_color = is_color_image(template_color_img)

    if original_is_color != template_is_color:
        print("\nObject not detected: Image and Template have different color types.")
        return

    # Find coordinates
    top_left, bottom_right, confidence_score = find_template_coordinates(original_color_img, template_color_img)

    print(f"\nTemplate matching confidence score : {round(confidence_score, 4)}")

    if confidence_score < 0.8:  # Minimum initial match requirement
        print("Object not detected: Initial template match score too low.")
        return

    # Verify cropped match and draw/save
    match_template_with_coordinates(
        original_img=original_color_img,
        template_img=template_color_img,
        top_left=top_left,
        bottom_right=bottom_right,
        match_threshold=0.9,
        original_filename=original_filename
    )

# --- Main entry ---
if __name__ == "__main__":
    perform_full_template_matching()
