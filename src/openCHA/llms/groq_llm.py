import os
from typing import Any, List
from langchain_groq import ChatGroq
from openCHA.llms.llm import BaseLLM


class GroqLLM(BaseLLM):

    model_name: str = "llama-3.3-70b-versatile"
    temperature: float = 0.1
    groq_api_key: str = ""

    class Config:
        arbitrary_types_allowed = True

    def generate(self, query: str, **kwargs) -> str:
        client = ChatGroq(
            model=self.model_name,
            temperature=self.temperature,
            api_key=self.groq_api_key
        )
        response = client.invoke(query)
        return response.content

    def _parse_response(self, response: Any) -> str:
        return str(response)

    def _prepare_prompt(
        self,
        query: str,
        history: str = "",
        meta: List[str] = None,
        previous_actions: List[Any] = None,
        use_history: bool = False,
        **kwargs
    ) -> str:
        return query