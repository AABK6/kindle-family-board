from __future__ import annotations

import concurrent.futures
import hashlib
import ipaddress
import os
import socket
from dataclasses import dataclass
from pathlib import Path

import paramiko


DEFAULT_USER = "root"
CONNECT_TIMEOUT = 3.0
DEFAULT_SERIAL = "90231703323302CF"
DEFAULT_KEY_PATH = Path(r"C:\Users\aabec\OneDrive\Documents\Playground\kindle_fix\id_rsa")
DEFAULT_HOST_CACHE = Path(r"C:\Users\aabec\OneDrive\Documents\Playground\kindle_fix\last_host.txt")


@dataclass(slots=True)
class KindleAuth:
    host: str
    user: str
    secret_label: str


def derive_passwords(serial: str) -> list[str]:
    serial = serial.strip()
    candidates: list[str] = []
    seen: set[str] = set()
    for value in (serial, serial.lower()):
        digest = hashlib.md5(f"{value}\n".encode("ascii")).hexdigest()
        for start, end in ((7, 11), (13, 17)):
            password = "fiona" + digest[start:end]
            if password not in seen:
                seen.add(password)
                candidates.append(password)
    return candidates


def configured_serial() -> str:
    return os.getenv("KFB_KINDLE_SERIAL", DEFAULT_SERIAL)


def configured_user() -> str:
    return os.getenv("KFB_KINDLE_USER", DEFAULT_USER)


def configured_host() -> str | None:
    value = os.getenv("KFB_KINDLE_HOST")
    return value.strip() if value and value.strip() else None


def configured_key_path() -> Path:
    raw = os.getenv("KFB_SSH_KEY_PATH")
    return Path(raw).expanduser() if raw else DEFAULT_KEY_PATH


def configured_host_cache_path() -> Path:
    raw = os.getenv("KFB_KINDLE_HOST_CACHE")
    return Path(raw).expanduser() if raw else DEFAULT_HOST_CACHE


def current_network() -> tuple[str, ipaddress.IPv4Network]:
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    try:
        sock.connect(("1.1.1.1", 53))
        local_ip = sock.getsockname()[0]
    finally:
        sock.close()
    return local_ip, ipaddress.ip_network(f"{local_ip}/24", strict=False)


def port_open(ip: str, port: int = 22, timeout: float = 0.35) -> bool:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        return sock.connect_ex((ip, port)) == 0
    finally:
        sock.close()


def read_banner(ip: str, timeout: float = 1.0) -> str:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.settimeout(timeout)
    try:
        sock.connect((ip, 22))
        data = sock.recv(256)
        return data.decode("ascii", "ignore")
    except OSError:
        return ""
    finally:
        sock.close()


def find_candidates(network: ipaddress.IPv4Network, skip_ip: str) -> list[str]:
    hosts = [str(ip) for ip in network.hosts() if str(ip) != skip_ip]
    discovered: list[str] = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=48) as pool:
        futures = {pool.submit(port_open, ip): ip for ip in hosts}
        for future in concurrent.futures.as_completed(futures):
            ip = futures[future]
            try:
                if future.result():
                    discovered.append(ip)
            except OSError:
                continue
    return discovered


def candidate_hosts() -> list[str]:
    local_ip, network = current_network()
    candidates: list[str] = []
    seen: set[str] = set()

    for preferred in (configured_host(), read_cached_host()):
        if preferred and preferred not in seen:
            seen.add(preferred)
            candidates.append(preferred)

    for discovered in find_candidates(network, local_ip):
        if discovered not in seen:
            seen.add(discovered)
            candidates.append(discovered)
    return candidates


def discover_host() -> str:
    candidates = candidate_hosts()
    fallback: list[str] = []
    for ip in candidates:
        banner = read_banner(ip)
        if "dropbear" in banner.lower() or "kindle" in banner.lower():
            return ip
        fallback.append(ip)
    if len(fallback) == 1:
        return fallback[0]
    local_ip, network = current_network()
    raise RuntimeError(f"No Kindle SSH host found on {network}")


def cache_host(host: str) -> None:
    cache_path = configured_host_cache_path()
    try:
        cache_path.parent.mkdir(parents=True, exist_ok=True)
        cache_path.write_text(host.strip(), encoding="ascii")
    except OSError:
        pass


def read_cached_host() -> str | None:
    cache_path = configured_host_cache_path()
    try:
        value = cache_path.read_text(encoding="ascii").strip()
    except OSError:
        return None
    return value or None


def connect(host: str | None = None, *, serial: str | None = None, user: str | None = None) -> tuple[paramiko.SSHClient, KindleAuth]:
    chosen_user = user or configured_user()
    chosen_serial = serial or configured_serial()
    key_path = configured_key_path()
    explicit_host = host is not None
    candidate_list = [host] if explicit_host else candidate_hosts()
    if not candidate_list:
        chosen_host = discover_host()
        candidate_list = [chosen_host]

    last_error: Exception | None = None
    last_host: str | None = None

    for chosen_host in candidate_list:
        if not chosen_host:
            continue
        if not explicit_host and not port_open(chosen_host, timeout=0.8):
            continue
        last_host = chosen_host

        if key_path.exists():
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                key = paramiko.RSAKey.from_private_key_file(str(key_path))
                client.connect(
                    hostname=chosen_host,
                    username=chosen_user,
                    pkey=key,
                    timeout=CONNECT_TIMEOUT,
                    look_for_keys=False,
                    allow_agent=False,
                    auth_timeout=CONNECT_TIMEOUT,
                )
                cache_host(chosen_host)
                return client, KindleAuth(host=chosen_host, user=chosen_user, secret_label=f"key:{key_path}")
            except Exception as exc:
                last_error = exc
                client.close()

        for password in derive_passwords(chosen_serial):
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            try:
                client.connect(
                    hostname=chosen_host,
                    username=chosen_user,
                    password=password,
                    timeout=CONNECT_TIMEOUT,
                    look_for_keys=False,
                    allow_agent=False,
                    auth_timeout=CONNECT_TIMEOUT,
                )
                cache_host(chosen_host)
                return client, KindleAuth(host=chosen_host, user=chosen_user, secret_label="derived-password")
            except Exception as exc:
                last_error = exc
                client.close()

    if last_host is None:
        local_ip, network = current_network()
        raise RuntimeError(f"No Kindle SSH host found on {network}")

    raise RuntimeError(f"SSH auth failed for {last_host}: {last_error}")


def exec_command(client: paramiko.SSHClient, command: str, timeout: float = 30.0) -> tuple[int, str, str]:
    stdin, stdout, stderr = client.exec_command(command, timeout=timeout)
    out = stdout.read().decode("utf-8", "ignore")
    err = stderr.read().decode("utf-8", "ignore")
    code = stdout.channel.recv_exit_status()
    return code, out, err
