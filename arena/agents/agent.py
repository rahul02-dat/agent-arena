from typing import Any, Dict
from arena.agents.base import BaseAgent

class LLMAgent(BaseAgent):
    def observe(self, observation: Any) -> None:
        self.memory.write(f"Observation: {observation}")

    def act(self) -> Dict[str, Any]:
        context = self.memory.read()
        
        system_prompt = (
            f"You are {self.identity} with role {self.role.name}. "
            "Examine the context and choose a tool to take action. "
            "You must use a tool."
        )
        
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Context history:\n{context}\n\nChoose your next tool action."}
        ]
        
        formatted_tools = []
        for tool in self.tools:
            formatted_tools.append({
                "type": "function",
                "function": {
                    "name": tool.name,
                    "description": tool.description,
                    "parameters": tool.input_schema
                }
            })
            
        response = self.model.chat(messages=messages, tools=formatted_tools)
        
        if "error" in response:
            return {"error": response["error"]}
            
        message = response.get("message", {})
        
        if message.get("tool_calls"):
            tool_call = message["tool_calls"][0]
            func = tool_call.get("function", {})
            return {
                "tool": func.get("name"),
                "command": func.get("arguments", {}).get("command")
            }
            
        return {"tool": "none", "content": message.get("content", "No response.")}
