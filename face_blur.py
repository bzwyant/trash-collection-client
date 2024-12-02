import cv2
import argparse
import base64
import numpy as np

def blur_faces(image_data, blur_factor=99):

    image_bytes = np.frombuffer(base64.b64decode(image_data), np.uint8)
    image = cv2.imdecode(image_bytes, cv2.IMREAD_COLOR)

    # Load the pre-trained face detection model
    face_cascade = cv2.CascadeClassifier(
        cv2.data.haarcascades + 'haarcascade_frontalface_default.xml'
    )

    # Convert to grayscale for face detection
    gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)

    # Detect faces
    faces = face_cascade.detectMultiScale(
        gray,
        scaleFactor=1.1,
        minNeighbors=5,
        minSize=(30, 30)
    )

    print(f"Found {len(faces)} faces in the image")

    # Blur each detected face
    for (x, y, w, h) in faces:
        # Extract the face region
        face_roi = image[y:y+h, x:x+w]
        # Apply Gaussian blur
        blurred_face = cv2.GaussianBlur(face_roi, (blur_factor, blur_factor), 30)
        # Replace the original face with the blurred version
        image[y:y+h, x:x+w] = blurred_face

    # Convert the processed image to bytes
    _, buffer = cv2.imencode('.jpg', image)
    
    # Convert to base64 string
    base64_image = base64.b64encode(buffer).decode()
    return base64_image

def main():
    parser = argparse.ArgumentParser(description='Blur faces in an image')
    parser.add_argument('input', help='Path to input image')
    parser.add_argument('output', help='Path to save output image')
    parser.add_argument('--blur', type=int, default=99,
                      help='Blur intensity (must be odd number), default=99')
    
    args = parser.parse_args()
    
    try:
        blur_faces(args.input, args.output, args.blur)
    except Exception as e:
        print(f"Error processing image: {str(e)}")

if __name__ == "__main__":
    main()