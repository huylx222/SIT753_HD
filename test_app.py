import os
import sys
import unittest
import json
import base64
import requests
import socketio
import time
import cv2
import numpy as np
from io import BytesIO

# Add parent directory to path for importing the API
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

class TestAPIWithImages(unittest.TestCase):
    """Test the face detection API with real images"""

    def setUp(self):
        """Set up for the tests"""
        # API endpoint URL
        self.api_url = "http://localhost:5001"
        
        # Test image paths
        self.test_image1_path = "test_image1.jpg"
        self.test_image2_path = "test_image2.jpg"
        
        # Check if test images exist
        for img_path in [self.test_image1_path, self.test_image2_path]:
            self.assertTrue(os.path.exists(img_path), f"Test image {img_path} not found")
        
        # Set up Socket.IO client
        self.sio = socketio.Client()
        self.sio_connected = False
        self.image_result = None
        
        # Define Socket.IO event handlers
        @self.sio.event
        def connect():
            self.sio_connected = True
            print("Socket.IO connected")
        
        @self.sio.event
        def disconnect():
            self.sio_connected = False
            print("Socket.IO disconnected")
        
        @self.sio.event
        def image_result(data):
            self.image_result = data
            print(f"Received image result: {len(str(data))} bytes")
        
        # Connect to Socket.IO server
        try:
            self.sio.connect(self.api_url)
            time.sleep(1)  # Wait for connection to establish
        except Exception as e:
            print(f"Socket.IO connection failed: {e}")
    
    def tearDown(self):
        """Clean up after tests"""
        if self.sio_connected:
            self.sio.disconnect()
    
    def test_api_health(self):
        """Test API health endpoint"""
        response = requests.get(f"{self.api_url}/test")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["status"], "success")
        self.assertEqual(data["message"], "API is working")
    
    def test_image1_detection(self):
        """Test face detection on test_image1.jpg"""
        self._test_image_detection(self.test_image1_path)
    
    def test_image2_detection(self):
        """Test face detection on test_image2.jpg"""
        self._test_image_detection(self.test_image2_path)
    
    def _test_image_detection(self, image_path):
        """Helper method to test face detection on a specific image"""
        # Reset the image_result
        self.image_result = None
        
        # Read the image and convert to base64
        with open(image_path, "rb") as img_file:
            img_data = img_file.read()
            base64_data = base64.b64encode(img_data).decode('utf-8')
        
        # Verify image is valid
        np_arr = np.frombuffer(img_data, np.uint8)
        img = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        self.assertIsNotNone(img, f"Failed to read image: {image_path}")
        
        # Print image dimensions
        height, width = img.shape[:2]
        print(f"Testing image: {image_path}, dimensions: {width}x{height}")
        
        # Send image to API
        self.sio.emit('image_frame', {
            'image': base64_data,
            'filename': os.path.basename(image_path)
        })
        
        # Wait for the response
        timeout = 10  # seconds
        start_time = time.time()
        while self.image_result is None and time.time() - start_time < timeout:
            time.sleep(0.1)
        
        # Assert we got a result
        self.assertIsNotNone(self.image_result, f"No response received for {image_path} after {timeout} seconds")
        
        # Validate the response structure
        self.assertIn('faces', self.image_result, "Response missing 'faces' field")
        self.assertIn('image_width', self.image_result, "Response missing 'image_width' field")
        self.assertIn('image_height', self.image_result, "Response missing 'image_height' field")
        
        # Check image dimensions match
        self.assertEqual(self.image_result['image_width'], width, "Image width doesn't match")
        self.assertEqual(self.image_result['image_height'], height, "Image height doesn't match")
        
        # If faces were detected, validate face data
        if self.image_result['faces']:
            print(f"Detected {len(self.image_result['faces'])} faces in {image_path}")
            
            for i, face in enumerate(self.image_result['faces']):
                # Check face structure
                self.assertIn('bbox', face, "Face missing bounding box")
                self.assertIn('confidence', face, "Face missing confidence score")
                
                # Check bbox structure
                bbox = face['bbox']
                self.assertIn('xmin', bbox, "Bounding box missing xmin")
                self.assertIn('ymin', bbox, "Bounding box missing ymin")
                self.assertIn('xmax', bbox, "Bounding box missing xmax")
                self.assertIn('ymax', bbox, "Bounding box missing ymax")
                
                # Check bbox values are sensible
                self.assertGreaterEqual(bbox['xmin'], 0, "xmin should be >= 0")
                self.assertGreaterEqual(bbox['ymin'], 0, "ymin should be >= 0")
                self.assertLessEqual(bbox['xmax'], width, "xmax should be <= image width")
                self.assertLessEqual(bbox['ymax'], height, "ymax should be <= image height")
                self.assertLess(bbox['xmin'], bbox['xmax'], "xmin should be < xmax")
                self.assertLess(bbox['ymin'], bbox['ymax'], "ymin should be < ymax")
                
                # Check confidence score
                self.assertGreaterEqual(face['confidence'], 0, "Confidence should be >= 0")
                self.assertLessEqual(face['confidence'], 1, "Confidence should be <= 1")
                
                # Check for spoof detection results if available
                if 'spoof_results' in self.image_result and i < len(self.image_result['spoof_results']):
                    spoof_result = self.image_result['spoof_results'][i]
                    
                    # Check for spoof_prob in the result
                    self.assertIn('spoof_prob', spoof_result, "Spoof result missing spoof_prob field")
                    
                    # Get the probability
                    spoof_prob = spoof_result['spoof_prob']
                    self.assertGreaterEqual(spoof_prob, 0, "Spoof probability should be >= 0")
                    self.assertLessEqual(spoof_prob, 1, "Spoof probability should be <= 1")
                    
                    # Determine if it's a spoof based on the threshold
                    is_spoof = spoof_prob > 0.2
                    
                    # Print spoof detection result
                    print(f"Face {i+1} spoof detection: {'Spoof' if is_spoof else 'Real'} "
                          f"with probability {spoof_prob:.4f}")
        else:
            print(f"No faces detected in {image_path}")
    
    def test_invalid_image(self):
        """Test behavior with an invalid image"""
        # Reset the image_result
        self.image_result = None
        
        # Create an invalid image (just random bytes)
        invalid_data = os.urandom(1000)
        base64_data = base64.b64encode(invalid_data).decode('utf-8')
        
        # Send invalid image to API
        self.sio.emit('image_frame', {
            'image': base64_data,
            'filename': 'invalid.jpg'
        })
        
        # Wait for the response
        time.sleep(3)
        
        # Check the API handled the invalid input gracefully
        # Note: The response could be None (indicating an error was emitted instead)
        # or it could be a structured error response
        if self.image_result is not None:
            # If we got a result, it should either have an 'error' field or empty 'faces'
            if 'error' in self.image_result:
                print(f"API correctly reported error: {self.image_result['error']}")
            else:
                self.assertIn('faces', self.image_result)
                self.assertEqual(len(self.image_result['faces']), 0, 
                                "Invalid image should result in no faces detected")
        # If self.image_result is None, the API might have emitted an 'error' event instead

if __name__ == '__main__':
    unittest.main()
    # testing