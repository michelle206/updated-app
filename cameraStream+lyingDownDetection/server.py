import socket
from PIL import Image
import io
import cv2
import struct

# Open the camera
cam = cv2.VideoCapture(0)
frame_width = int(cam.get(cv2.CAP_PROP_FRAME_WIDTH))
frame_height = int(cam.get(cv2.CAP_PROP_FRAME_HEIGHT))

def sendCameraStream(conn):
    while True:
        ret, frame = cam.read()
        
        if not ret:
            print("Failed to grab frame")
            break

        # Display the captured frame
        cv2.imshow('Camera', frame)

        # Press 'q' to exit the loop
        if cv2.waitKey(1) == ord('q'):
            break
        
        # Encode the frame as JPEG
        _, buffer = cv2.imencode('.jpg', frame)
        
        # Get the size of the buffer
        buffer_size = len(buffer)
        
        # Send the size of the buffer first (as a 4-byte integer)
        conn.sendall(struct.pack(">I", buffer_size))
        
        # Send the actual image data
        conn.sendall(buffer)

    cam.release()
    cv2.destroyAllWindows()

# Create a socket and listen for incoming connections
with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
    s.bind(('localhost', 12345))
    s.listen(1)
    print("Waiting for a connection...")
    
    conn, addr = s.accept()
    with conn:
        print(f"Connected by {addr}")
        sendCameraStream(conn)
