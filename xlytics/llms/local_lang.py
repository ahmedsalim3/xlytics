from typing import Dict
import requests

from ..config.config import ModelConfig


class LocalLLM:
    def __init__(self, config: ModelConfig, base_model: str) -> None:
        self.config = config
        self.base_model = base_model
        self.model_platform: str | None = None  # 'ollama' or 'groq'
        self.llm_model = self._get_llm_model()

    def _get_llm_model(self) -> Dict[str, str | None]:
        model_list = self.config.models_list()
        ollama_models = model_list.get("OLLAMA_MODELS_LIST", [])
        groq_models = model_list.get("GROQ_MODELS_LIST", [])

        # Check which platform the model is available on
        if self.base_model in ollama_models:
            self.model_platform = "ollama"
            return {
                "platform": "ollama",
                "model": self.base_model,
                "base_url": self.config.env_config.get("OLLAMA_BASE_URL"),
                "api_key": None,  # Ollama doesn't require API key for local models
            }
        elif self.base_model in groq_models:
            self.model_platform = "groq"
            return {
                "platform": "groq",
                "model": self.base_model,
                "base_url": self.config.env_config.get("GROQ_BASE_URL"),
                "api_key": self.config.env_config.get("GROQ_API_KEY"),
            }
        else:
            raise ValueError(
                f"Model {self.base_model} not found in either "
                f"Ollama ({ollama_models}) or Groq ({groq_models}) models"
            )

    def generate(
        self,
        prompt: str,
        system_prompt: str = "",
        max_tokens: int = 1000,
        temperature: float = 0.7,
    ) -> str:
        """
        Generate text using the loaded model
        """
        if self.model_platform == "ollama":
            return self._generate_ollama(prompt, system_prompt, max_tokens, temperature)
        elif self.model_platform == "groq":
            return self._generate_groq(prompt, system_prompt, max_tokens, temperature)
        else:
            raise ValueError(f"Unknown model platform: {self.model_platform}")

    def _generate_ollama(
        self, prompt: str, system_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """
        Generate text using Ollama API
        """
        url = f"{self.llm_model['base_url']}/api/generate"

        payload = {
            "model": self.llm_model["model"],
            "prompt": f"{system_prompt}\n\n{prompt}" if system_prompt else prompt,
            "stream": False,
            "options": {"num_predict": max_tokens, "temperature": temperature},
        }

        response = requests.post(url, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            raise Exception(
                f"Ollama API error: {response.status_code} - {response.text}"
            )

    def _generate_groq(
        self, prompt: str, system_prompt: str, max_tokens: int, temperature: float
    ) -> str:
        """
        Generate text using Groq API
        """
        url = f"{self.llm_model['base_url']}/chat/completions"
        headers = {
            "Authorization": f"Bearer {self.llm_model['api_key']}",
            "Content-Type": "application/json",
        }

        # Prepare messages array
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": self.llm_model["model"],
            "messages": messages,
            "max_tokens": max_tokens,
            "temperature": temperature,
        }

        response = requests.post(url, json=payload, headers=headers)
        if response.status_code == 200:
            return response.json()["choices"][0]["message"]["content"]
        else:
            raise Exception(f"Groq API error: {response.status_code} - {response.text}")

    def get_model_info(self) -> Dict[str, str]:
        """
        Get information about the loaded model
        """
        return {
            "platform": self.model_platform,
            "model_name": self.base_model,
            "base_url": self.llm_model["base_url"],
        }
