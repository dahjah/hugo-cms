import abc
import os
import requests
import json
from typing import Dict, Any, Optional

class BaseLLMProvider(abc.ABC):
    @abc.abstractmethod
    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        """Generates JSON output from the LLM."""
        pass

class OpenAICompatibleProvider(BaseLLMProvider):
    """Generic provider for OpenAI, Perplexity, Grok, etc."""
    
    def __init__(self, api_key: str, base_url: str, model: str):
        self.api_key = api_key
        self.base_url = base_url
        self.model = model

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": self.model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            "response_format": {"type": "json_object"}
        }
        
        response = requests.post(f"{self.base_url}/chat/completions", headers=headers, json=payload)
        response.raise_for_status()
        
        content = response.json()['choices'][0]['message']['content']
        return json.loads(content)

class GeminiProvider(BaseLLMProvider):
    """Provider for Google Gemini API."""
    
    def __init__(self, api_key: str, model: str = "gemini-pro"):
        self.api_key = api_key
        self.model = model
        self.url = f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent?key={api_key}"

    def generate_json(self, system_prompt: str, user_prompt: str) -> Dict[str, Any]:
        headers = {"Content-Type": "application/json"}
        
        # Gemini doesn't always support 'system' role in v1beta consistently via REST, 
        # so we prepend it to user prompt or use strict structure if using v1beta.
        # But let's try the modern message structure.
        
        payload = {
            "contents": [{
                "parts": [{"text": f"SYSTEM INSTRUCTION: {system_prompt}\n\nUSER REQUEST: {user_prompt}"}]
            }],
            "generationConfig": {
                "response_mime_type": "application/json"
            }
        }
        
        response = requests.post(self.url, headers=headers, json=payload)
        response.raise_for_status()
        
        result = response.json()
        content = result['candidates'][0]['content']['parts'][0]['text']
        return json.loads(content)

def get_provider() -> Optional[BaseLLMProvider]:
    """Factory to get the configured provider based on ENV."""
    
    # 1. OpenAI (or compatible)
    if os.environ.get("OPENAI_API_KEY"):
        return OpenAICompatibleProvider(
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ.get("OPENAI_BASE_URL", "https://api.openai.com/v1"),
            model=os.environ.get("OPENAI_MODEL", "gpt-4-turbo-preview")
        )
        
    # 2. Perplexity
    elif os.environ.get("PERPLEXITY_API_KEY"):
        return OpenAICompatibleProvider(
            api_key=os.environ["PERPLEXITY_API_KEY"],
            base_url="https://api.perplexity.ai",
            model="sonar-medium-online" # or configured
        )
        
    # 3. Gemini
    elif os.environ.get("GEMINI_API_KEY"):
        return GeminiProvider(
            api_key=os.environ["GEMINI_API_KEY"]
        )
        
    # 4. Grok (xAI)
    elif os.environ.get("XAI_API_KEY"):
         return OpenAICompatibleProvider(
            api_key=os.environ["XAI_API_KEY"],
            base_url="https://api.x.ai/v1",
            model="grok-beta"
        )
        
    return None
