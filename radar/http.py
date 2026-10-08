"""Small curl transport, using the operating system's verified TLS trust store."""
import json
import os
import hashlib
from pathlib import Path
import subprocess
import time
from urllib.parse import urlparse


class SourceError(RuntimeError):
    pass


class Client:
    def __init__(self, delay=0.6):
        self.delay = delay
        self.last = 0.0

    def text(self, url, payload=None):
        if urlparse(url).scheme != "https":
            raise SourceError("Only HTTPS sources are supported")
        cache = os.environ.get("RADAR_HTTP_CACHE")
        cache_file = None
        if cache:
            key = hashlib.sha256((url + json.dumps(payload, sort_keys=True)).encode()).hexdigest()
            cache_file = Path(cache) / (key + ".txt")
            if cache_file.exists() and time.time() - cache_file.stat().st_mtime < 3600:
                return cache_file.read_text()
        time.sleep(max(0, self.delay - (time.monotonic() - self.last)))
        cmd = ["curl", "--silent", "--show-error", "--location", "--proto", "=https",
               "--proto-redir", "=https", "--connect-timeout", "15", "--max-time", "45",
               "--retry", "2", "--retry-delay", "2", "--fail-with-body",
               "--user-agent", "JobSkillRadar/0.1 (+https://github.com/jieera/job-skill-radar)",
               "--header", "Accept: application/json, text/html", url]
        if payload is not None:
            cmd += ["--header", "Content-Type: application/json", "--data-binary", "@-"]
        try:
            result = subprocess.run(cmd, input=json.dumps(payload) if payload is not None else None,
                                    text=True, capture_output=True, timeout=150)
        except (OSError, subprocess.TimeoutExpired) as exc:
            raise SourceError(f"Transport unavailable: {type(exc).__name__}") from exc
        finally:
            self.last = time.monotonic()
        if result.returncode:
            raise SourceError(f"Request failed ({urlparse(url).hostname}): {result.stderr.strip()[:200]}")
        if not result.stdout.strip():
            raise SourceError("Empty response; source may require browser access")
        if cache_file:
            cache_file.parent.mkdir(parents=True, exist_ok=True)
            cache_file.write_text(result.stdout)
        return result.stdout

    def json(self, url, payload=None):
        try:
            return json.loads(self.text(url, payload))
        except json.JSONDecodeError as exc:
            raise SourceError("Expected JSON; received a page or an access challenge") from exc
