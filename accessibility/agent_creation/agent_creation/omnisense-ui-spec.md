# OmniSense – Spec Driven Development (SDD)

## 1. Project Overview
**Application Name**: OmniSense

OmniSense is an AI-powered environmental awareness interface that listens and analyzes audio or visual signals from the environment and alerts users to important events (e.g., baby crying, alarms, glass breaking).

The system is designed for:
- Accessibility
- Safety monitoring
- Ambient AI interaction
- Emergency detection

The UI must provide a clean, futuristic, “wow-factor” experience with a light color palette, subtle animations, and responsive design.

## 2. Architecture
### 2.1 Tech Stack
**Frontend**
- React 18
- Vite
- TailwindCSS
- Framer Motion (animations)
- React Icons
- WebSocket client

**Backend**
- Express.js
- Node.js
- Socket.IO
- Audio processing API
- AI classification service (future)

## 3. Design Principles
### 3.1 UI Philosophy
The UI should feel:
- Intelligent
- Calm
- Futuristic
- Friendly
- Accessible

### 3.2 Visual Style
**Theme**: Light futuristic dashboard

**Primary Color Palette**:
| Element | Color |
| :--- | :--- |
| Primary | #6C7CFF |
| Secondary | #A8B1FF |
| Accent | #FF6B6B |
| Background | #F5F7FF |
| Card | #FFFFFF |
| Text | #1A1A2E |
| Border | #E4E7FF |

### 3.3 Wow Factor Requirements
The UI must include:
- soft glow effects
- subtle gradients
- glassmorphism cards
- animated sound pulse when listening
- smooth transitions
- floating SOS button

## 4. Responsive Design
The UI must support:

**Mobile**
- width: 320px – 768px
- single column layout
- larger touch buttons
- bottom anchored actions

**Desktop**
- width: 1024px+
- centered dashboard
- max width container
- card-based layout

**Breakpoints**:
- mobile: 0 - 768px
- tablet: 768px - 1024px
- desktop: 1024px+

## 5. Application Layout
**Global Layout Structure**
```
App
 ├── Header
 ├── ModeSelector
 ├── ListenerCard
 ├── EventAlert
 ├── StartListeningButton
 └── SOSFloatingButton
```

## 6. UI Components Specification
### 6.1 Header Component
**Purpose**: Displays application branding and system status.

**Layout**
- **Left**: Shield icon, OmniSense title
- **Right**: Status indicator (Critical / Normal), Language selector, Senior Mode toggle

**Props**
- status: "normal" | "warning" | "critical"
- language: string
- seniorMode: boolean

**Behavior**
- Status color changes dynamically
- Senior Mode increases font size
- Language dropdown triggers localization

### 6.2 Mode Selector
Two tabs: Vision, Audio

**UI Behavior**
- Active tab has: gradient highlight, subtle glow, smooth sliding indicator

**Props**
- mode: "vision" | "audio"
- onModeChange()

### 6.3 Environmental Listener Card
Main interaction component.

**Content**
- **Top**: Large microphone icon, animated pulse ring
- **Title**: Environmental Listener
- **Description**: Tap to analyze environmental sounds

**Animation**
- When active: microphone pulse animation, glowing rings expand outward

### 6.4 Event Alert Component
Displays detected events.

**Example Event**: ⚠ Baby crying - A baby is crying nearby. Please check on the baby's well-being.

**Severity Levels**
| Level | Color |
| :--- | :--- |
| Info | Blue |
| Warning | Orange |
| Critical | Red |

**Props**: eventType, message, severity, timestamp

### 6.5 Start Listening Button
Primary action button.

**Style**: Rounded, Gradient, Soft glow, Hover animation
**Text**: Start Listening (or "Listening..." when active)
**States**: idle, listening, processing

### 6.6 SOS Floating Button
**Position**: Bottom-left corner.
**Style**: Red circular button, Shadow glow, Floating animation
**Behavior**: When clicked, triggers emergency workflow, opens emergency modal

## 7. Animations
Animations must be subtle and modern.
- **Microphone Pulse**: scale: 1 → 1.2, opacity: 1 → 0, duration: 1.5s, repeat: infinite
- **Button Hover**: scale: 1 → 1.05, shadow glow increase
- **Alert Entry**: fade + slide up, duration: 300ms

## 8. Accessibility
Must support: ARIA labels, screen readers, large text (senior mode), keyboard navigation, high contrast mode.

## 9. API Specification (Express)
**Base URL**: `/api`
- **Start Listening**: `POST /listen/start` -> `{ status: "listening" }`
- **Stop Listening**: `POST /listen/stop`
- **Event Detection**: `GET /events` -> `{ eventType: "baby_crying", severity: "warning", message: "A baby is crying nearby." }`

## 10. WebSocket Events
Server pushes real-time events.
**Channel**: `/events`
**Example message**: `{ type: "environment_event", data: { eventType: "baby_crying", severity: "warning" } }`

## 11. Folder Structure
```
omnisense
 ├── client
 │   ├── components
 │   │   ├── Header.jsx
 │   │   ├── ModeSelector.jsx
 │   │   ├── ListenerCard.jsx
 │   │   ├── EventAlert.jsx
 │   │   ├── StartButton.jsx
 │   │   └── SOSButton.jsx
 │   │
 │   ├── pages
 │   │   └── Dashboard.jsx
 │   │
 │   ├── hooks
 │   │   └── useSocket.js
 │   │
 │   └── App.jsx
 │
 ├── server
 │   ├── routes
 │   │   └── listen.js
 │   │
 │   ├── sockets
 │   │   └── events.js
 │   │
 │   └── server.js
 │
 └── omnisense-ui-spec.md
```

## 12. Future Features
- **AI Detection**: baby crying, glass breaking, smoke alarm, dog barking, human distress
- **Vision Mode**: fall detection, fire detection, motion detection
- **Smart Notifications**: push alerts, emergency contacts, wearable integrations

## 13. Performance Requirements
- First load < 1.5s
- Interaction latency < 100ms
- Mobile optimized bundle
- Lazy loaded components

## 14. Security
- HTTPS required
- microphone permission handling
- rate limiting
- authentication layer for advanced features

## 15. Definition of Done
- responsive on mobile + desktop
- animations implemented
- API integration working
- accessibility tested
- unit tests written
