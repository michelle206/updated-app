import cv2

cap = cv2.VideoCapture(0)

# Check if the webcam opened successfully
if not cap.isOpened():
    print("Error: Could not open webcam.")
    exit()

# Continuously capture frames from the webcam
while True:
    # Capture frame-by-frame
    ret, frame = cap.read()
    print(frame)
    
    if not ret:
        print("Failed to grab frame")
        break

    # Display the frame in a window
    cv2.imshow('Webcam Feed', frame)

    # Exit the webcam feed window if 'q' is pressed
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Release the webcam and close windows
cap.release()
cv2.destroyAllWindows()