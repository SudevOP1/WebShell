from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import traceback, json

from utils.models import WSConnectionsManager
from utils.helpers import print_debug, print_log


app = FastAPI()
DEBUG = True
manager = WSConnectionsManager(DEBUG)


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
            print_debug(DEBUG, f"recieved: {data}", "WEBSOCKET")
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
        print_log(f"something went wrong: {e}\n{traceback_str}", "ERROR")
