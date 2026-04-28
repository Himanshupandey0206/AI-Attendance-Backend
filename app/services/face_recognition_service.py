import cv2
import numpy as np
import face_recognition
import base64
from typing import List, Tuple, Optional

def decode_base64_image(base64_string: str) -> np.ndarray:
    """Decodes a base64 image string to an OpenCV image."""
    if ',' in base64_string:
        base64_string = base64_string.split(',')[1]
    
    img_data = base64.b64decode(base64_string)
    nparr = np.frombuffer(img_data, np.uint8)
    img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
    return img

def get_face_encoding(image_base64: str) -> Optional[List[float]]:
    """Extracts face encoding from a base64 image."""
    try:
        img = decode_base64_image(image_base64)
        
        # Convert the image from BGR color (which OpenCV uses) to RGB color
        rgb_img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # Find all the faces and face encodings in the image
        face_locations = face_recognition.face_locations(rgb_img)
        if not face_locations:
            return None # No face found
        
        # Only take the first face found
        face_encodings = face_recognition.face_encodings(rgb_img, face_locations)
        if not face_encodings:
            return None
            
        return face_encodings[0].tolist()
    except Exception as e:
        print(f"Error in get_face_encoding: {e}")
        return None

def verify_face(known_encoding: List[float], image_base64: str, tolerance: float = 0.6) -> bool:
    """Verifies if the face in the image matches the known encoding."""
    try:
        unknown_encoding = get_face_encoding(image_base64)
        if not unknown_encoding:
            return False
        
        # Compare faces
        results = face_recognition.compare_faces(
            [np.array(known_encoding)], 
            np.array(unknown_encoding),
            tolerance=tolerance
        )
        return bool(results[0])
    except Exception as e:
        print(f"Error in verify_face: {e}")
        return False
