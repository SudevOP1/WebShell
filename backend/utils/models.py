from fastapi import WebSocket

from .helpers import print_debug


class WSConnectionsManager:

    def __init__(self, debug: bool):
        self.debug = debug
        self.active_connections: list[WebSocket] = []
        print_debug(self.debug, f"manager initialized")

    async def connect(self, websocket: WebSocket) -> None:
        await websocket.accept()
        self.active_connections.append(websocket)
        print_debug(
            self.debug,
            f"1 client connected, current active clients = {len(self.active_connections)}",
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        self.active_connections.remove(websocket)
        print_debug(
            self.debug,
            f"1 client disconnected, current active clients = {len(self.active_connections)}",
        )

    async def send_personal_msg(self, websocket: WebSocket, msg: str) -> None:
        await websocket.send_text(msg)

    async def broadcast_msg(self, msg: str) -> None:
        for connection in self.active_connections:
            await connection.send_text(msg)
