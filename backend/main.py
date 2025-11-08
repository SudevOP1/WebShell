from fastapi import FastAPI, WebSocket, WebSocketDisconnect
import traceback, json, time

from utils.models import WSConnectionsManager, WSConnection
from utils.helpers import print_debug, print_log
from settings import *


app = FastAPI()
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

    # send initial output
    await manager.send_personal_msg(
        websocket,
        {"type": "output", "output": connection.terminal.get_output_queue()},
    )

    try:
        while True:
            if websocket in manager.connections.keys():
                data = await websocket.receive_text()
                print_debug(DEBUG, f"recieved: {data}", "WS")

                # decode data and check proper format
                data = json.loads(data)
                msg_type = data.get("type", None)
                if not isinstance(msg_type, str):
                    await manager.send_personal_msg(
                        websocket,
                        {"type": "error", "error": "invalid 'type' string field"},
                    )
                    continue

                # received cmd to be run
                if data.get("type") == "cmd":

                    # cmd field necessary
                    cmd = data.get("cmd", None)
                    if cmd is None or not isinstance(cmd, str):
                        await manager.send_personal_msg(
                            websocket,
                            {"type": "error", "error": "invalid 'cmd' string field"},
                        )
                        continue

                    # timeout field not necessary, default = 5.0
                    timeout = data.get("timeout", 5.0)
                    if timeout is not None and not isinstance(timeout, float):
                        await manager.send_personal_msg(
                            websocket,
                            {"type": "error", "error": "invalid 'timeout' float field"},
                        )
                        continue

                    # check if cmd in ALLOWED_CMD_LIST
                    cmd_name = cmd.split(" ")[0].strip()
                    if cmd_name not in ALLOWED_CMD_LIST:
                        await manager.send_personal_msg(
                            websocket,
                            {
                                "type": "output",
                                "output": f"{cmd}\r\n'{cmd_name}' command not allowed\r\n\r\n{connection.terminal.run_cmd('', 1.0)}",
                            },
                        )
                        continue

                    # run the cmd and return output after timeout seconds
                    connection = manager.get_connection(websocket)
                    output = connection.terminal.run_cmd(cmd, timeout)
                    await manager.send_personal_msg(
                        websocket,
                        {"type": "output", "output": output},
                    )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)

    except Exception as e:
        traceback_str = traceback.format_exc()
        print_log(f"something went wrong: {e}\n{traceback_str}", "ERROR")
