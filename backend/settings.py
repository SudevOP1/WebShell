from dotenv import load_dotenv
import os

load_dotenv()
GITHUB_CLIENT_ID = os.getenv("GITHUB_CLIENT_ID")
GITHUB_CLIENT_SECRET = os.getenv("GITHUB_CLIENT_SECRET")
FRONTEND_URL = os.getenv("FRONTEND_URL")
JWT_SECRET = os.getenv("JWT_SECRET")

DEBUG = True
LOGS_FILENAME = "logs.txt"
ALLOWED_CMD_LIST = [
    "ls",
    "echo",
    "dir",
]

debug_error = "ERROR"
debug_debug = "DEBUG"
debug_auth = "AUTH"
debug_ws = "WS"
debug_manager = "MANAGER"
