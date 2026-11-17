"""AI Provider service for LLM completions and dense embeddings."""
import hashlib
import logging
import math
from abc import ABC, abstractmethod
from typing import Any

from openai import AsyncOpenAI

from researchpilot.core.config import get_settings

logger = logging.getLogger(__name__)


class AIProvider(ABC):
    """Abstract AI Provider for text generation and vector embeddings."""

    @abstractmethod
    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        """Generate dense embedding vectors for a batch of text chunks."""

    @abstractmethod
    async def chat_complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        """Call chat completion model."""


class OpenAIProvider(AIProvider):
    """Real OpenAI client integration."""

    def __init__(self):
        settings = get_settings()
        self.settings = settings
        if not settings.openai_api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not configured.")
        self.client = AsyncOpenAI(api_key=settings.openai_api_key)

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        response = await self.client.embeddings.create(
            model=self.settings.openai_embedding_model,
            input=texts,
        )
        return [item.embedding for item in response.data]

    async def chat_complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        kwargs: dict[str, Any] = {
            "model": self.settings.openai_chat_model,
            "messages": messages,
            "temperature": temperature,
        }
        if response_format:
            kwargs["response_format"] = response_format

        response = await self.client.chat.completions.create(**kwargs)
        return response.choices[0].message.content or ""


class MockAIProvider(AIProvider):
    """Deterministic offline AI Provider for testing and CI/CD without API keys."""

    def __init__(self, dimensions: int = 1536):
        self.dimensions = dimensions

    async def get_embeddings(self, texts: list[str]) -> list[list[float]]:
        results: list[list[float]] = []
        for text in texts:
            # Deterministic bag-of-words hash embedding so identical terms correlate
            vec = [0.0] * self.dimensions
            words = text.lower().split()
            for word in words:
                h = int(hashlib.sha256(word.encode()).hexdigest(), 16)
                idx = h % self.dimensions
                vec[idx] += 1.0

            # Normalize
            norm = math.sqrt(sum(x * x for x in vec))
            if norm > 0:
                vec = [x / norm for x in vec]
            else:
                vec[0] = 1.0
            results.append(vec)
        return results

    async def chat_complete(
        self,
        messages: list[dict[str, str]],
        temperature: float = 0.2,
        response_format: dict[str, Any] | None = None,
    ) -> str:
        last_msg = messages[-1]["content"] if messages else ""
        if "plan" in last_msg.lower() or "research plan" in last_msg.lower():
            return """{
                "objective": "Evaluate deep learning architectures for brain tumor detection.",
                "sub_questions": [
                    "What are the dominant convolutional and transformer architectures used in MRI segmentation?",
                    "What validation metrics and benchmarks are used across papers?"
                ],
                "steps": [
                    {"step_order": 1, "step_type": "retrieval", "title": "Retrieve model architecture passages"},
                    {"step_order": 2, "step_type": "analysis", "title": "Compare quantitative performance metrics"}
                ],
                "comparison_dimensions": ["Architecture", "Dataset", "Dice Score", "Limitations"],
                "expected_sections": ["Executive Summary", "Thematic Synthesis", "Method Comparison", "Limitations"]
            }"""
        return "Deterministic synthetic response based on uploaded corpus."


def get_ai_provider() -> AIProvider:
    """Factory to obtain AI provider based on environment configuration."""
    settings = get_settings()
    if settings.openai_api_key and settings.openai_api_key.strip():
        return OpenAIProvider()
    return MockAIProvider(dimensions=settings.embedding_dimensions)
