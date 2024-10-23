import org.bytedeco.javacv.*;
import org.bytedeco.opencv.opencv_core.*;
import org.bytedeco.opencv.opencv_dnn.*;
import org.bytedeco.opencv.opencv_imgproc.*;

import static org.bytedeco.opencv.global.opencv_core.*;
import static org.bytedeco.opencv.global.opencv_dnn.*;
import static org.bytedeco.opencv.global.opencv_imgproc.*;

public class PoseEstimation {
    public static void main(String[] args) throws FrameGrabber.Exception {
        // Load the pre-trained OpenPose model files
        String protoPath = "path_to_pose_deploy_linevec.prototxt";
        String modelPath = "path_to_pose_iter_440000.caffemodel";

        Net net = readNetFromCaffe(protoPath, modelPath);

        // Start capturing video from the webcam
        OpenCVFrameGrabber grabber = new OpenCVFrameGrabber(0);
        grabber.start();

        CanvasFrame frame = new CanvasFrame("Pose Estimation", CanvasFrame.getDefaultGamma() / grabber.getGamma());

        // Set the parameters
        int inWidth = 368;
        int inHeight = 368;
        double threshold = 0.1;

        while (frame.isVisible()) {
            // Capture a frame from the webcam
            Frame videoFrame = grabber.grab();
            Mat mat = new OpenCVFrameConverter.ToMat().convert(videoFrame);

            if (mat != null) {
                // Prepare the frame for pose estimation
                Mat inputBlob = blobFromImage(mat, 1.0 / 255.0, new Size(inWidth, inHeight), new Scalar(0, 0, 0), false, false);

                // Set the input for the neural network
                net.setInput(inputBlob);

                // Run the forward pass to get the output of the model
                Mat output = net.forward();

                int H = output.size(2);
                int W = output.size(3);

                // Loop through the detected keypoints
                for (int n = 0; n < 15; n++) {  // 15 body parts for OpenPose model
                    Mat heatMap = output.slice(n);

                    Core.MinMaxLocResult mm = Core.minMaxLoc(heatMap);
                    Point p = new Point((int)(mm.maxLoc.x * mat.cols() / W), (int)(mm.maxLoc.y * mat.rows() / H));

                    if (mm.maxVal > threshold) {
                        // Draw circles around detected keypoints
                        circle(mat, p, 5, new Scalar(0, 255, 255), -1);
                    }
                }

                // Show the processed frame
                frame.showImage(new OpenCVFrameConverter.ToMat().convert(mat));
            }
        }

        grabber.stop();
        frame.dispose();
    }
}
