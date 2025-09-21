# Design

## Architecture
- **Backend**: FastAPI server with WebSocket endpoints
- **Frontend**: Next.js application with chat interface

## Backend Components
- `main.py`: FastAPI app with WebSocket handlers
- WebSocket endpoints: `/ws/admin` and `/ws/user`
- Bidirectional streaming communication

## Frontend Components
- Navigation bar with Admin/User tabs
- Chat interface for each tab
- WebSocket client connections to respective endpoints
- Real-time message display and input

## Communication Flow
```
Frontend (Next.js) <--WebSocket--> Backend (FastAPI)
    Admin Tab      <---> /ws/admin
    User Tab       <---> /ws/user
```
