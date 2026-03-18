from __future__ import annotations

import os
import socket
from pathlib import Path

from dotenv import load_dotenv

from .config import ROOT_DIR


def load_repo_env() -> Path:
    env_path = ROOT_DIR / ".env"
    load_dotenv(env_path, override=False)
    return env_path


def current_local_ip() -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("1.1.1.1", 53))
        return sock.getsockname()[0]
    finally:
        sock.close()


def server_port(default: int = 8765) -> int:
    value = os.getenv("KFB_SERVER_PORT")
    return int(value) if value else default

