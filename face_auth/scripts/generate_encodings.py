import face_recognition
import pickle
import cv2
import os
from imutils import paths

# Define paths
dataset_path = "datasets"
encoding_file = "encodings.pickle"

# Check if dataset directory exists
if not os.path.isdir(dataset_path):
    raise FileNotFoundError(f"The directory {dataset_path} does not exist.")

print("[INFO] Start processing faces...")
imagePaths = list(paths.list_images(dataset_path))

# Initialize the list of known encodings and known names
knownEncodings = []
knownNames = []

# Loop over the image paths
for (i, imagePath) in enumerate(imagePaths):
    # Extract the person name from the image path
    print(f"[INFO] Processing image {i + 1}/{len(imagePaths)}")
    name = imagePath.split(os.path.sep)[-2]

    # Load the input image and convert it from BGR (OpenCV ordering) to RGB
    image = cv2.imread(imagePath)
    if image is None:
        print(f"[WARNING] Unable to load image: {imagePath}")
        continue

    rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    # Detect the (x, y)-coordinates of the bounding boxes corresponding to each face
    boxes = face_recognition.face_locations(rgb, model="hog")

    # Compute the facial embeddings for the faces
    encodings = face_recognition.face_encodings(rgb, boxes)

    # Add each encoding + name to our list of known names and encodings
    for encoding in encodings:
        knownEncodings.append(encoding)
        knownNames.append(name)

# Serialize the facial encodings + names to disk
print("[INFO] Serializing encodings...")
data = {"encodings": knownEncodings, "names": knownNames}

with open(encoding_file, "wb") as f:
    f.write(pickle.dumps(data))

print(f"[INFO] Encodings serialized to {encoding_file}")
