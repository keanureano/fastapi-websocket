from typing import List
from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
from fastapi.templating import Jinja2Templates
from fastapi.responses import HTMLResponse

app = FastAPI()
templates = Jinja2Templates(directory="templates")


class ConnectionManager:

    def __init__(self):
        self.active_connections: List[WebSocket] = []

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        self.active_connections.append(websocket)

    def disconnect(self, websocket: WebSocket):
        self.active_connections.remove(websocket)

    async def send_personal_message(self, message: str, websocket: WebSocket):
        await websocket.send_text(message)

    async def broadcast(self, message: str, websocket: WebSocket):
        for connection in self.active_connections:
            if (connection == websocket):
                continue
            await connection.send_text(message)


connectionmanager = ConnectionManager()


@app.get("/", response_class=HTMLResponse)
async def read_index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.websocket("/ws/{client_id}")
async def websocket_endpoint(websocket: WebSocket, client_id: int):
    # accept connections
    await connectionmanager.connect(websocket)
    try:
        while True:
            data = await websocket.receive_text()
            await connectionmanager.send_personal_message(f"User{client_id} (You): {data}", websocket)
            await connectionmanager.broadcast(f"User{client_id}: {data}", websocket)

    except WebSocketDisconnect:
        connectionmanager.disconnect(websocket)
        await connectionmanager.broadcast(f"User{client_id} left the chat")
