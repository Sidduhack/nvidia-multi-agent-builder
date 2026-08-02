"""NVIDIA NIM provider adapter."""
from __future__ import annotations
import json, os, time
from dataclasses import dataclass
from typing import Any
from urllib import error, request
DEFAULT_BASE_URL = "https://integrate.api.nvidia.com/v1"
class NvidiaProviderError(RuntimeError): pass
@dataclass(frozen=True)
class NvidiaConfig:
    api_key: str
    base_url: str = DEFAULT_BASE_URL
    timeout_seconds: float = 60.0
    max_retries: int = 2
    @classmethod
    def from_env(cls):
        key=os.getenv("NVIDIA_API_KEY","").strip()
        if not key: raise NvidiaProviderError("NVIDIA_API_KEY is not configured")
        return cls(key,os.getenv("NVIDIA_BASE_URL",DEFAULT_BASE_URL).rstrip("/"),float(os.getenv("NVIDIA_TIMEOUT_SECONDS","60")),int(os.getenv("NVIDIA_MAX_RETRIES","2")))
class NvidiaProvider:
    def __init__(self, config=None): self.config=config or NvidiaConfig.from_env()
    def chat_completion(self, *, model:str, messages:list[dict[str,Any]], max_tokens:int=2048, temperature:float=.2, top_p:float=.9):
        if not model.strip(): raise ValueError("model is required")
        if not messages: raise ValueError("messages must not be empty")
        body=json.dumps({"model":model,"messages":messages,"max_tokens":max_tokens,"temperature":temperature,"top_p":top_p,"stream":False}).encode()
        for attempt in range(self.config.max_retries+1):
            req=request.Request(f"{self.config.base_url}/chat/completions",data=body,method="POST",headers={"Authorization":f"Bearer {self.config.api_key}","Content-Type":"application/json","Accept":"application/json"})
            try:
                with request.urlopen(req,timeout=self.config.timeout_seconds) as response: return json.loads(response.read().decode())
            except error.HTTPError as exc:
                if (exc.code==429 or 500<=exc.code<600) and attempt<self.config.max_retries: time.sleep(min(2**attempt,4)); continue
                raise NvidiaProviderError(f"NVIDIA API request failed with HTTP {exc.code}") from exc
            except (error.URLError,TimeoutError,json.JSONDecodeError) as exc:
                if attempt<self.config.max_retries: time.sleep(min(2**attempt,4)); continue
                raise NvidiaProviderError("NVIDIA API request failed") from exc
        raise NvidiaProviderError("NVIDIA API request failed")
