from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import traceback, json

from utils.models import WSConnectionsManager


app = FastAPI()
DEBUG = True
manager = WSConnectionsManager()


@app.get("/hi")
def hi():
    return {
        "success": True,
        "msg": "hi",
    }


@app.get("/healthz")
def health_check():
    return {
        "success": True,
        "status": "ok",
    }


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await manager.connect(websocket)

    try:
        while True:
            data = await websocket.receive_text()
            print(f"[WEBSOCKET] recieved: {data}")
            data = json.loads(data)

            if data.get("type") == "echo":
                await manager.send_personal_msg(
                    websocket,
                    json.dumps(
                        {
                            "type": "echo_return",
                            "msg": data.get("msg", ""),
                        }
                    ),
                )

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as e:
        traceback_str = traceback.format_exc()
        print(f"[ERROR] something went wrong: {e}\n{traceback_str}")
