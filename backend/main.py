from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from jose import jwt, JWTError
from jose.exceptions import ExpiredSignatureError
import traceback, json, time

from utils.models import WSConnectionsManager, WSConnection
from utils.helpers import *
from routes.auth_routes import auth_router
from settings import *


app = FastAPI()
app.include_router(auth_router, prefix="/auth")
app.add_middleware(
    CORSMiddleware,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    allow_origins=[
        "http://localhost:3000",
    ],
)

manager = WSConnectionsManager()


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
        print_debug(f"something wen wrong: {e}\n{traceback.format_exc()}", debug_error)
        return {
            "success": False,
            "error": f"something wen wrong: {e}",
            "traceback": traceback.format_exc(),
        }


@app.websocket("/ws")
async def ws(websocket: WebSocket):

    # accepting websocket first, then inspecting cookies
    await websocket.accept()

    # inspecting cookies
    cookies = websocket.cookies
    token = cookies.get("session", None)

    # checking jwt token
    if token is None:
        await websocket.send_json(
            {"type": "error", "error": "unauthorized: missing session token"}
        )
        print_debug("unauthorized request denied", debug_ws)
        return

    # validating jwt token
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=["HS256"])
        username = payload.get("sub", None)
        if username is None:
            raise JWTError("invalid payload")
        print_debug(f"authenticated user: {username}", debug_auth, log_to_file=True)

    # expired jwt token
    except ExpiredSignatureError:
        print_debug("jwt token expired", debug_debug)
        await websocket.send_json(
            {"type": "error", "error": "unauthorized: invalid token"}
        )
        await websocket.close()
        return

    # invalid jwt token
    except JWTError:
        print_debug("jwt authentication failed", debug_error)
        await websocket.send_json(
            {"type": "error", "error": "unauthorized: invalid token"}
        )
        await websocket.close()
        return

    # handle other unexpected errors
    except Exception as e:
        print_debug(
            f"something went wrong: {e}\n{traceback.format_exc()}",
            label=debug_error,
            log_to_file=True,
        )
        await websocket.close()
        return

    # jwt token validated, create connection object
    connection = WSConnection(websocket)
    await manager.add_connection(connection)

    # send initial terminal output
    await manager.send_personal_msg(
        websocket,
        {"type": "output", "output": connection.terminal.get_output_queue()},
    )

    try:
        while True:
            if websocket in manager.connections.keys():
                data = await websocket.receive_text()
                print_debug(f"recieved: {data}", debug_ws)

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
                    print_log(
                        msg=f"[{username}] ran command: {cmd}",
                        label=debug_ws,
                        log_to_file=True,
                    )

    except WebSocketDisconnect:
        await manager.disconnect(websocket)

    except Exception as e:
        print_debug(
            f"something went wrong: {e}\n{traceback.format_exc()}",
            label=debug_error,
            log_to_file=True,
        )
