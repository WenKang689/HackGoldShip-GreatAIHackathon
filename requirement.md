# Requirements

## Functional Requirements
- **Backend**: WebSocket server for real-time communication
- **Frontend**: Next.js chat interface with Admin/User tabs
- Send and receive streaming messages
- Support for chatbot integration
- Tab-based navigation between Admin and User interfaces

## Technical Requirements
### Backend
- FastAPI framework
- WebSocket protocol
- Python 3.8+

### Frontend
- Next.js framework
- WebSocket client
- React components for chat interface
- Node.js 18+

## Usage
### Backend
```bash
cd agent/
pip install -r requirements.txt
python main.py
```

### Frontend
```bash
cd frontend/
npm install
npm run dev
```

## Endpoints
- Backend WebSocket: `ws://localhost:8000/ws/admin` and `ws://localhost:8000/ws/user`
- Frontend: `http://localhost:3000`
