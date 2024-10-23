import cv2
import numpy as np

# Load the pre-trained MobileNet SSD model and prototxt file
model_path = "MobileNetSSD_deploy.caffemodel"
config_path = "MobileNetSSD_deploy.prototxt"
net = cv2.dnn.readNetFromCaffe(config_path, model_path)

# List of class labels MobileNet SSD was trained to detect
class_labels = ["background", "aeroplane", "bicycle", "bird", "boat", 
                "bottle", "bus", "car", "cat", "chair", "cow", "diningtable",
                "dog", "horse", "motorbike", "person", "pottedplant", 
                "sheep", "sofa", "train", "tvmonitor"]

# Open webcam
cap = cv2.VideoCapture(0)

# Set webcam resolution (optional)
cap.set(3, 640)  # Set width
cap.set(4, 480)  # Set height

while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    if not ret:
        print("Failed to capture frame")
        break
    
    # Prepare the frame for object detection
    h, w = frame.shape[:2]
    blob = cv2.dnn.blobFromImage(cv2.resize(frame, (300, 300)), 0.007843, (300, 300), 127.5)

    # Set the blob as input to the network
    net.setInput(blob)
    detections = net.forward()

    # Loop over the detections
    for i in range(detections.shape[2]):
        # Extract the confidence (probability) for each detection
        confidence = detections[0, 0, i, 2]

        # Filter out weak detections with confidence less than 0.2
        if confidence > 0.2:
            # Get the class label index and the bounding box coordinates
            class_id = int(detections[0, 0, i, 1])
            box = detections[0, 0, i, 3:7] * np.array([w, h, w, h])
            (startX, startY, endX, endY) = box.astype("int")

            # Draw the bounding box and label on the frame
            label = f"{class_labels[class_id]}: {confidence:.2f}"
            cv2.rectangle(frame, (startX, startY), (endX, endY), (0, 255, 0), 2)
            y = startY - 15 if startY - 15 > 15 else startY + 15
            cv2.putText(frame, label, (startX, y), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 255, 0), 2)

    # Display the frame with object detection
    cv2.imshow("Object Detection", frame)

    # Break the loop if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()
