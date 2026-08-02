from .model_registry import ModelRoute, model_for_agent
def route_agent(agent_name:str)->ModelRoute: return model_for_agent(agent_name)
