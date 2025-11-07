from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import traceback, json, time

from utils.models import WSConnectionsManager, WSConnection
from utils.helpers import print_debug, print_log


app = FastAPI()
DEBUG = True
manager = WSConnectionsManager(DEBUG)


@app.get("/healthz")
def health_check():
    try:
        start_time = time.time()
        return {
            "success": True,
            "health": {
                "status": "ok",
                "num_active_connections": len(manager.connections),
                "time_required": round(time.time() - start_time, 2),
            },
        }
    except Exception as e:
        return {
            "success": False,
            "health": {"status": "error", "error": str(e)},
        }


@app.websocket("/ws")
async def ws(websocket: WebSocket):
    await websocket.accept()
    connection = WSConnection(websocket)
    await manager.add_connection(connection)
    await manager.send_personal_msg(
        websocket,
        {"type": "output", "output": connection.terminal.get_output_queue()},
    )

    try:
        while True:
            data = await websocket.receive_text()
            print_debug(DEBUG, f"recieved: {data}", "WEBSOCKET")
            data = json.loads(data)

            msg_type = data.get("type", None)
            if not isinstance(msg_type, str):
                await manager.send_personal_msg(
                    websocket,
                    {"type": "error", "error": "invalid 'type' string field"},
                )
                continue

            if data.get("type") == "cmd":
                cmd = data.get("cmd", None)
                timeout = data.get("timeout", 5.0)
                if cmd is None or not isinstance(cmd, str):
                    await manager.send_personal_msg(
                        websocket,
                        {"type": "error", "error": "invalid 'cmd' string field"},
                    )
                    continue
                if timeout is not None and not isinstance(timeout, float):
                    await manager.send_personal_msg(
                        websocket,
                        {"type": "error", "error": "invalid 'timeout' float field"},
                    )
                    continue
                else:
                    connection = manager.get_connection(websocket)
                    output = connection.terminal.run_cmd(cmd, timeout)
                    await manager.send_personal_msg(
                        websocket,
                        {"type": "output", "output": output},
                    )

    except WebSocketDisconnect:
        manager.disconnect(websocket)

    except Exception as e:
        traceback_str = traceback.format_exc()
        print_log(f"something went wrong: {e}\n{traceback_str}", "ERROR")
