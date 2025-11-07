from fastapi import WebSocket
import winpty, re, queue, time, threading, json

from .helpers import print_debug


class WSConnection:

    def __init__(self, websocket: WebSocket):
        self.websocket = websocket
        self.terminal = PseudoTerminal()


class WSConnectionsManager:

    def __init__(self, debug: bool):
        self.debug = debug
        self.connections: dict[WebSocket, WSConnection] = {}
        print_debug(self.debug, f"manager initialized")

    def get_connection(self, websocket: WebSocket) -> WSConnection | None:
        return self.connections.get(websocket, None)

    async def add_connection(self, connection: WSConnection) -> None:
        self.connections[connection.websocket] = connection
        print_debug(
            self.debug,
            f"1 client connected, current active clients = {len(self.connections)}",
        )

    async def disconnect(self, websocket: WebSocket) -> None:
        connection = self.get_connection(websocket)
        if connection is not None:
            connection.terminal.close()
            print_debug(
                self.debug,
                f"1 client disconnected, current active clients = {len(self.connections)}",
            )

    async def send_personal_msg(self, websocket: WebSocket, msg: str) -> None:
        connection = self.get_connection(websocket)
        if connection is not None:
            await connection.websocket.send_text(json.dumps(msg))
            print_debug(self.debug, f"sent personal msg: {msg}", "WEBSOCKET")

    async def broadcast_msg(self, msg: str) -> None:
        for connection in self.connections:
            await connection.websocket.send_text(msg)
            print_debug(self.debug, f"broadcasted msg: {msg}", "WEBSOCKET")


class PseudoTerminal:

    def __init__(self, shell: str = "cmd.exe", cwd="C:\\"):
        self.pty: winpty.PtyProcess = winpty.PtyProcess.spawn(shell, cwd)
        self.output_queue: queue.Queue = queue.Queue()
        self._stop_flag: bool = False
        self.reader_thread = threading.Thread(target=self._read_output, daemon=True)
        self.reader_thread.start()

    def _clean_output(self, data: str) -> str:
        """remove ANSI escape codes to prevent garbage text"""
        return (re.sub(r"\x1b\[[0-9;?]*[A-Za-z]", "", data)).replace("\r\n", "\n")

    def _read_output(self) -> None:
        """continuously keep reading pty output and store in queue"""
        while not self._stop_flag:
            try:
                data = self.pty.read()
                if data:
                    self.output_queue.put(self._clean_output(data))
            except EOFError:
                break
            except Exception as e:
                self.output_queue.put(f"\nError reading: {e}")
                break

    def get_output_queue(self, timeout: float = 5.0) -> str:
        """return and clear the output queue"""

        time.sleep(timeout)
        output = ""
        while not self.output_queue.empty():
            output += self.output_queue.get_nowait()

        return output.strip()

    def run_cmd(self, cmd: str, timeout: float = 5.0) -> str:
        """run a cmd in self.pty and return output"""

        # clear queue if any
        while not self.output_queue.empty():
            self.output_queue.get_nowait()

        # send cmd (\r\n = enter for windows)
        self.pty.write(cmd + "\r\n")

        # wait a bit for the output
        time.sleep(timeout)

        output = ""
        while not self.output_queue.empty():
            output += self.output_queue.get_nowait()

        return output.strip()

    def close(self):
        self._stop_flag = True
        try:
            self.pty.close(True)
        except Exception as e:
            pass


if __name__ == "__main__":
    terminal = PseudoTerminal()

    print(terminal.get_output_queue(), end="")
    for cmd in ["echo hello", "dir"]:
        print(terminal.run_cmd(cmd), end="")

    terminal.close()
