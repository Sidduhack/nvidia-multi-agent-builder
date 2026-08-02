import os
from dataclasses import dataclass
@dataclass(frozen=True)
class ModelRoute:
    provider:str
    model:str
DEFAULT_MODEL="openai/gpt-oss-120b"
def model_for_agent(agent_name:str)->ModelRoute:
    key="NVIDIA_MODEL_"+agent_name.upper().replace("-","_")
    model=os.getenv(key,os.getenv("NVIDIA_DEFAULT_MODEL",DEFAULT_MODEL)).strip()
    if not model: raise ValueError(f"No model configured for agent {agent_name}")
    return ModelRoute("nvidia",model)
