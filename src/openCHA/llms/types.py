from typing import Dict
from typing import Type
from openCHA.llms.llm import BaseLLM
from openCHA.llms.llm_types import LLMType
from openCHA.llms.anthropic import AntropicLLM
from openCHA.llms.openai import OpenAILLM
from openCHA.llms.groq_llm import GroqLLM

LLM_TO_CLASS: Dict[LLMType, Type[BaseLLM]] = {
    LLMType.OPENAI: OpenAILLM,
    LLMType.ANTHROPIC: AntropicLLM,
    LLMType.GROQ: GroqLLM,        # ← ADDed new
}