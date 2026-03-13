const express = require('express');
const http = require('http');
const { Server } = require('socket.io');
const cors = require('cors');
const dotenv = require('dotenv');
const path = require('path');

dotenv.config();

const app = express();
app.use(cors());
app.use(express.json());

const server = http.createServer(app);
const io = new Server(server, {
  cors: {
    origin: "*",
    methods: ["GET", "POST"]
  }
});

const PORT = process.env.PORT || 3001;

// API Routes
app.post('/api/listen/start', (req, res) => {
  console.log('Start listening triggered');
  res.json({ status: "listening" });
});

app.post('/api/listen/stop', (req, res) => {
  console.log('Stop listening triggered');
  res.json({ status: "idle" });
});

app.get('/api/events', (req, res) => {
  res.json([
    {
      id: "1",
      eventType: "system_ready",
      severity: "info",
      message: "OmniSense systems are online and calibrated.",
      timestamp: new Date()
    }
  ]);
});

// Socket.IO Logic
io.on('connection', (socket) => {
  console.log('Client connected:', socket.id);

  socket.on('disconnect', () => {
    console.log('Client disconnected:', socket.id);
  });

  // Example: Push an event every 30 seconds for demo
  /*
  setInterval(() => {
    socket.emit('environment_event', {
      type: "environment_event",
      data: {
        id: Math.random().toString(36).substr(2, 9),
        eventType: "background_noise",
        severity: "info",
        message: "Ambient noise levels are normal.",
        timestamp: new Date()
      }
    });
  }, 30000);
  */
});

server.listen(PORT, () => {
  console.log(`OmniSense Server running on port ${PORT}`);
});
