import cv2
import base64
import requests
from pathlib import Path
from PIL import Image

from ..commons.logger import Logger
from ..config.config import ModelConfig

logger = Logger()


class LlavaModel:
    def __init__(self, config: ModelConfig):
        self.config = config
        self.base_url = config.get("OLLAMA_BASE_URL")
        self.model_name = config.get("VISION_MODEL")

    def analyze(self, image, prompt: str, system_prompt: str = "") -> str:
        temp_path = "temp_llava_img.jpg"
        try:
            pil_image = Image.fromarray(cv2.cvtColor(image, cv2.COLOR_BGR2RGB))
            pil_image.save(temp_path)

            with open(temp_path, "rb") as f:
                image_data = base64.b64encode(f.read()).decode("utf-8")

            combined_prompt = f"{system_prompt}\n\n{prompt}" if system_prompt else prompt

            payload = {
                "model": self.model_name,
                "prompt": combined_prompt,
                "images": [image_data],
                "stream": False,
            }

            response = requests.post(f"{self.base_url}/api/generate", json=payload)
            if response.status_code == 200:
                return response.json().get("response", "No description available.")
            else:
                logger.error(f"Ollama API returned {response.status_code}: {response.text}")
                return f"Error from Ollama: {response.status_code}"

        except Exception as e:
            logger.error(f"LLaVA request failed: {e}")
            return f"Error: {e}"

        finally:
            if Path(temp_path).exists():
                Path(temp_path).unlink()
