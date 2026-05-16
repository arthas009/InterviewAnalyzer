"""Interview preparation mode - generates questions and evaluates spoken answers."""

import logging
import uuid
from typing import Optional, Callable

from llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

QUESTION_GENERATION_PROMPT = """You are an expert interviewer. Generate a single interview question based on:
- Topic: {topic}
- Difficulty: {difficulty}
- Interview Type: {interview_type}

Rules:
- Generate exactly ONE question
- Make it realistic — something that would actually be asked in a real interview
- For coding questions, include a clear problem statement
- For behavioral questions, make them open-ended
- For system design, ask about designing a specific system
- Respond with ONLY the question text, nothing else"""

EVALUATION_PROMPT = """You are an expert interview evaluator. Evaluate the candidate's answer to an interview question.

Question: {question}

Candidate's Answer (transcribed from speech): {answer}

Evaluate and respond in this JSON format:
{{
  "score": <1-10>,
  "feedback": "Brief constructive feedback (2-3 sentences)",
  "strengths": ["strength 1", "strength 2"],
  "improvements": ["improvement 1", "improvement 2"],
  "ideal_answer": "A concise ideal answer (3-5 sentences)"
}}

Be fair but constructive. Consider that the answer was spoken, so minor speech artifacts are expected.
Answer in the same language as the question."""


class PrepEngine:
    """Engine for interview preparation mode."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        temperature: float = 0.5,
        max_tokens: int = 2048,
    ):
        self.llm = llm_provider
        self.temperature = temperature
        self.max_tokens = max_tokens

    async def generate_question(
        self,
        topic: str = "general programming",
        difficulty: str = "medium",
        interview_type: str = "technical",
    ) -> str:
        """Generate a single interview question."""
        prompt = QUESTION_GENERATION_PROMPT.format(
            topic=topic,
            difficulty=difficulty,
            interview_type=interview_type,
        )

        question = ""
        async for chunk in self.llm.stream_response(
            system_prompt=prompt,
            user_message=f"Generate a {difficulty} {interview_type} question about {topic}.",
            temperature=self.temperature,
            max_tokens=500,
        ):
            question += chunk

        return question.strip()

    async def evaluate_answer(
        self,
        question: str,
        answer: str,
        on_chunk: Optional[Callable[[str], None]] = None,
    ) -> str:
        """Evaluate a candidate's answer and return feedback."""
        prompt = EVALUATION_PROMPT.format(question=question, answer=answer)

        full_response = ""
        async for chunk in self.llm.stream_response(
            system_prompt="You are an expert interview evaluator. Respond only in valid JSON.",
            user_message=prompt,
            temperature=0.3,
            max_tokens=self.max_tokens,
        ):
            full_response += chunk
            if on_chunk:
                on_chunk(chunk)

        return full_response
