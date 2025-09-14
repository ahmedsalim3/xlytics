import logging
from datetime import datetime
from pathlib import Path

from ..config import config as CFG


class Logger:
    __instance = None

    def __new__(cls):
        if cls.__instance is None:
            cls.__instance = super().__new__(cls)
        return cls.__instance

    def __init__(self):
        if hasattr(self, "_initialized"):
            return
        self._initialized = True

        config = CFG.EnvConfig()

        self.log_level = int(config.get("LOG_LEVEL", logging.INFO))
        self.log_file = None

        log_file_name = config.get("LOG_FILE")
        if log_file_name:
            logs_dir = Path("output")
            logs_dir.mkdir(parents=True, exist_ok=True)
            self.log_file = str(logs_dir / log_file_name)

    def info(self, message):
        if self.log_level <= logging.INFO:
            self._log(message)

    def debug(self, message):
        if self.log_level <= logging.DEBUG:
            self._log(f"🕷️ {message}")

    def warning(self, message):
        if self.log_level <= logging.WARNING:
            self._log(f"⚠️ {message}")

    def error(self, message):
        if self.log_level <= logging.ERROR:
            self._log(f"🔴 {message}")

    def critical(self, message):
        if self.log_level <= logging.CRITICAL:
            self._log(f"💥 {message}")

    def _log(self, message):
        timestamp = datetime.now().strftime("%y-%m-%d %H:%M:%S")
        line = f"{timestamp} - {message}"
        print(line)
        if self.log_file:
            try:
                with open(self.log_file, "a", encoding="utf-8") as f:
                    f.write(line + "\n")
            except Exception:
                pass
