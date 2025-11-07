from fastapi import WebSocket


class WSConnectionsManager:

    def __init__(self):
        print(f"[DEBUG] manager initialized")
        self.active_connections: list[WebSocket] = []

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        print(
            f"[DEBUG] client connected, current active = {len(self.active_connections)}"
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)
        print(
            f"[DEBUG] client disconnected, current active = {len(self.active_connections)}"
        )

    async def send_personal_msg(self, websocket: WebSocket, msg: str) -> None:
        await websocket.send_text(msg)

    async def broadcast_msg(self, msg: str) -> None:
        for connection in self.active_connections:
            await connection.send_text(msg)
