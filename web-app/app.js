const express = require('express');
const multer = require('multer');
const path = require('path');
const axios = require('axios');
const fs = require('fs');
const socketIoClient = require('socket.io-client');
const app = express();
const port = 3000;

// Connect to the Python API WebSocket
const apiUrl = process.env.API_URL || 'http://localhost:5001';
console.log(`Connecting to API at: ${apiUrl}`);
const socket = socketIoClient(apiUrl);

socket.on('connect', () => {
  console.log('Connected to API socket server');
});

socket.on('connect_error', (error) => {
  console.error('Socket connection error:', error);
});

// Ensure uploads directory exists
const uploadDir = './uploads';
if (!fs.existsSync(uploadDir)) {
  fs.mkdirSync(uploadDir);
}

// Multer setup for file uploads
const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => cb(null, Date.now() + path.extname(file.originalname)),
});

const fileFilter = (req, file, cb) => {
  const allowedTypes = /jpeg|jpg|JPG|png|gif/;
  const extname = allowedTypes.test(path.extname(file.originalname).toLowerCase());
  const mimetype = allowedTypes.test(file.mimetype);
  if (extname && mimetype) cb(null, true);
  else cb(new Error('Only image files are allowed'));
};

const upload = multer({
  storage,
  limits: { fileSize: 10 * 1024 * 1024 }, // 10MB
  fileFilter,
});

// Serve static files if needed
app.use(express.static('public'));

// Upload endpoint
app.post('/upload', upload.single('image'), (req, res) => {
  if (!req.file) return res.status(400).json({ error: 'No file uploaded' });

  const imagePath = req.file.path;
  const imageBuffer = fs.readFileSync(imagePath);
  const base64Image = imageBuffer.toString('base64');

  // Timeout fallback (optional but recommended)
  const timeout = setTimeout(() => {
    fs.unlinkSync(imagePath);
    res.status(504).json({ error: 'API timeout' });
  }, 10000); // 10 seconds

  // Listen once for the response
  socket.once('image_result', (data) => {
    clearTimeout(timeout);
    fs.unlinkSync(imagePath);
    console.log('Received image_result:', data);
    res.json(data);
  });

  socket.once('error', (error) => {
    clearTimeout(timeout);
    fs.unlinkSync(imagePath);
    res.status(500).json({ error: error.message || 'API error' });
  });

  // Send the image to the Python API
  socket.emit('image_frame', {
    image: base64Image,
    filename: req.file.originalname,
  });
});

// API connectivity test
app.get('/test-api', async (req, res) => {
  try {
    const response = await axios.get(`${apiUrl}/test`);
    res.json({ message: 'Connection successful', apiResponse: response.data });
  } catch (error) {
    res.status(500).json({
      error: 'Failed to connect to API',
      details: error.message,
    });
  }
});

// Start server
app.listen(port, () => {
  console.log(`Web app running at http://localhost:${port}`);
});
