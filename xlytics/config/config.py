import os
from abc import ABC, abstractmethod
from enum import Enum
from typing import Dict

import requests
from dotenv import load_dotenv


class Mode(Enum):
    SEARCH = 1
    URL = 2


class __Config(ABC):
    @abstractmethod
    def load(self) -> Dict[str, str]:
        pass


class EnvConfig(__Config):
    def __init__(self):
        load_dotenv()

    def get(self, key: str, default=None) -> str:
        return os.getenv(key, default)

    def load(self) -> dict:
        load_dotenv()
        return {
            # Twitter API Keys
            "TWITTER_API_KEY": os.getenv("TWITTER_API_KEY"),
            "TWITTER_API_SECRET": os.getenv("TWITTER_API_SECRET"),
            "TWITTER_BEARER_TOKEN": os.getenv("TWITTER_BEARER_TOKEN"),
            "TWITTER_ACCESS_TOKEN": os.getenv("TWITTER_ACCESS_TOKEN"),
            "TWITTER_ACCESS_TOKEN_SECRET": os.getenv("TWITTER_ACCESS_TOKEN_SECRET"),
            # OLLAMA
            "OLLAMA_BASE_URL": os.getenv("OLLAMA_BASE_URL"),
            "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL"),
            # GROQ
            "GROQ_BASE_URL": os.getenv("GROQ_BASE_URL"),
            "GROQ_API_KEY": os.getenv("GROQ_API_KEY"),
            "GROQ_MODEL": os.getenv("GROQ_MODEL"),
            # Vision Models
            "VISION_MODEL": os.getenv("VISION_MODEL"),
            "YOLO_MODEL": os.getenv("YOLO_MODEL"),
            "YOLO_CONFIDENCE_THRESHOLD": os.getenv("YOLO_CONFIDENCE_THRESHOLD"),
            # DATABASE
            "DATABASE_PATH": os.getenv("DATABASE_PATH"),
            # LOGGING
            "LOG_LEVEL": os.getenv("LOG_LEVEL"),
            "LOG_FILE": os.getenv("LOG_FILE"),
            # OUTPUT
            "OUTPUT_NAME": os.getenv("OUTPUT_NAME", "output"),
        }


class ModelConfig(__Config):
    def __init__(self):
        self.env_config = EnvConfig()

    def __repr__(self):
        return "Groq and Ollama models are available"

    def get(self, key: str, default=None) -> str:
        return self.env_config.get(key, default)

    def load(self) -> Dict[str, str]:
        models = self.models_list()
        return {
            "GROQ_MODEL": os.getenv("GROQ_MODEL")
            or models.get("GROQ_MODELS_LIST", [None])[0],
            "OLLAMA_MODEL": os.getenv("OLLAMA_MODEL")
            or models.get("OLLAMA_MODELS_LIST", [None])[0],
            "YOLO_MODEL": os.getenv("YOLO_MODEL")
            or models.get("YOLO_MODELS_LIST", [None])[0],
        }

    def models_list(self) -> dict:
        groq_models = self._groq_models()
        ollama_models = self._ollama_models()
        yolo_models = self._yolo_models()
        return {
            "GROQ_MODELS_LIST": groq_models,
            "OLLAMA_MODELS_LIST": ollama_models,
            "YOLO_MODELS_LIST": yolo_models,
        }

    def _yolo_models(self) -> list:
        return [self.env_config.get("YOLO_MODEL")]

    def _groq_models(self) -> list:
        headers = {
            "Authorization": "Bearer {n}".format(n=self.env_config.get("GROQ_API_KEY"))
        }

        res = requests.get(
            self.env_config.get("GROQ_BASE_URL") + "/models", headers=headers
        )
        if res.status_code == 200:
            models = [model["id"] for model in res.json().get("data", [])]
            return models
        else:
            raise Exception(f"Failed to get models: {res.status_code} {res.text}")

    def _ollama_models(self) -> list:
        response = requests.get(self.env_config.get("OLLAMA_BASE_URL") + "/api/tags")
        if response.status_code == 200:
            models = response.json().get("models", [])
            return [model["name"] for model in models]
        else:
            raise Exception(
                f"Failed to fetch models: {response.status_code} - {response.text}"
            )


if __name__ == "__main__":
    config_loader = EnvConfig()
    settings = config_loader.load()
    for key, value in settings.items():
        print(f"{key}: {value}")

    model_config = ModelConfig()
    import pprint

    pprint.pprint(model_config.models_list())
