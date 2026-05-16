import asyncio
import logging
import time
import uuid
from dataclasses import dataclass, field
from typing import Optional, Callable, AsyncGenerator

from llm.base import BaseLLMProvider

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are an intelligent assistant. Your job is to analyze conversation transcripts and:

1. DETECT if a NEW question has been asked in the latest transcript segment.
2. If a question is detected, provide a helpful and comprehensive answer IN THE SAME LANGUAGE as the question.

Rules for detection:
- Identify ANY question being asked (technical, general knowledge, opinions, etc.)
- Ignore repeated questions you've already answered (check the "Previously detected questions" list)
- A question can be implicit (e.g., "Tell me about closures" is a question even without a question mark)
- Focus on the LATEST transcript segment — that's where new questions appear
- Ignore greetings and filler words
- IMPORTANT: Always answer in the same language the question was asked in

When you detect a question, respond in this EXACT JSON format:
{
  "detected": true,
  "question": "The extracted/cleaned-up question text",
  "answer": "Your comprehensive answer here. Be concise but thorough. Answer in the SAME LANGUAGE as the question."
}

If NO new question is detected, respond with ONLY:
{"detected": false}

Keep answers focused and practical. Include code examples for coding questions. For complex topics, use bullet points for clarity."""


@dataclass
class DetectedQA:
    """A detected question-answer pair."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    question: str = ""
    answer: str = ""
    timestamp: float = field(default_factory=time.time)


class QuestionDetector:
    """Detects technical interview questions from transcript and generates answers."""

    def __init__(
        self,
        llm_provider: BaseLLMProvider,
        temperature: float = 0.3,
        max_tokens: int = 2048,
        buffer_max_chars: int = 3000,
        min_chars_before_analysis: int = 50,
    ):
        self.llm = llm_provider
        self.temperature = temperature
        self.max_tokens = max_tokens
        self.buffer_max_chars = buffer_max_chars
        self.min_chars_before_analysis = min_chars_before_analysis

        self._transcript_buffer: list[str] = []
        self._detected_questions: list[DetectedQA] = []
        self._is_analyzing = False
        self._pending_text: list[str] = []
        self._lock = asyncio.Lock()

    def add_transcript(self, text: str) -> None:
        """Add new transcript text to the buffer."""
        if text.strip():
            self._transcript_buffer.append(text.strip())
            self._pending_text.append(text.strip())

            # Trim buffer to max size
            full_text = " ".join(self._transcript_buffer)
            while len(full_text) > self.buffer_max_chars and len(self._transcript_buffer) > 1:
                self._transcript_buffer.pop(0)
                full_text = " ".join(self._transcript_buffer)

    async def analyze(
        self,
        on_question: Optional[Callable[[str, str], None]] = None,
        on_answer_chunk: Optional[Callable[[str, str], None]] = None,
        on_answer_complete: Optional[Callable[[str, str], None]] = None,
    ) -> Optional[DetectedQA]:
        """Analyze pending transcript text for new technical questions.

        Args:
            on_question: Callback(question_id, question_text) when question detected.
            on_answer_chunk: Callback(question_id, chunk) for streaming answer.
            on_answer_complete: Callback(question_id, full_answer) when answer complete.

        Returns:
            DetectedQA if a question was found, None otherwise.
        """
        async with self._lock:
            if self._is_analyzing:
                return None

            if not self._pending_text:
                return None

            # Wait until enough text accumulates before calling LLM
            pending_total = " ".join(self._pending_text)
            if len(pending_total) < self.min_chars_before_analysis:
                return None

            self._is_analyzing = True
            self._pending_text.clear()

        try:
            return await self._do_analysis(pending_total, on_question, on_answer_chunk, on_answer_complete)
        finally:
            self._is_analyzing = False

    async def _do_analysis(
        self,
        new_text: str,
        on_question: Optional[Callable[[str, str], None]],
        on_answer_chunk: Optional[Callable[[str, str], None]],
        on_answer_complete: Optional[Callable[[str, str], None]],
    ) -> Optional[DetectedQA]:
        """Perform the actual analysis."""
        # Build context
        previous_questions = "\n".join(
            f"- {qa.question}" for qa in self._detected_questions[-10:]
        ) or "None yet"

        full_transcript = " ".join(self._transcript_buffer)

        user_message = f"""Analyze this transcript for NEW questions.

FULL TRANSCRIPT (for context):
{full_transcript}

LATEST SEGMENT (focus here for new questions):
{new_text}

PREVIOUSLY DETECTED QUESTIONS (do NOT re-detect these):
{previous_questions}

IMPORTANT: Your answer MUST be in the same language as the transcript. If the transcript is in Turkish, answer in Turkish. If in English, answer in English.

Respond with the JSON format specified."""

        # Stream response from LLM
        full_response = ""
        async for chunk in self.llm.stream_response(
            system_prompt=SYSTEM_PROMPT,
            user_message=user_message,
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        ):
            full_response += chunk

        # Parse the response
        result = self._parse_response(full_response)
        if result is None:
            logger.debug(f"No question detected in: {new_text[:100]}")
            return None

        qa = DetectedQA(question=result["question"], answer=result["answer"])
        self._detected_questions.append(qa)
        logger.info(f"*** QUESTION DETECTED: {qa.question[:100]}")
        logger.info(f"*** ANSWER: {qa.answer[:100]}...")

        # Notify callbacks
        if on_question:
            on_question(qa.id, qa.question)

        # For streaming UX, we re-stream the answer
        if on_answer_chunk:
            # Stream answer in chunks for UI display
            chunk_size = 20  # characters per chunk for smooth streaming
            for i in range(0, len(qa.answer), chunk_size):
                chunk = qa.answer[i:i + chunk_size]
                on_answer_chunk(qa.id, chunk)
                await asyncio.sleep(0.02)  # Small delay for streaming effect

        if on_answer_complete:
            on_answer_complete(qa.id, qa.answer)

        return qa

    def _parse_response(self, response: str) -> Optional[dict]:
        """Parse the LLM JSON response."""
        import json
        import re

        # Try to extract JSON from the response
        response_text = response.strip()

        # Handle markdown code blocks
        if "```json" in response_text:
            start = response_text.index("```json") + 7
            end = response_text.index("```", start)
            response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.index("```") + 3
            end = response_text.index("```", start)
            response_text = response_text[start:end].strip()

        # Try to find any JSON object in the text
        json_match = re.search(r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}', response_text, re.DOTALL)
        if json_match:
            try:
                data = json.loads(json_match.group())
                if not data.get("detected"):
                    return None  # No question detected — this is normal
                if data.get("question") and data.get("answer"):
                    return {"question": data["question"], "answer": data["answer"]}
            except json.JSONDecodeError:
                pass

        # Direct parse attempt
        try:
            data = json.loads(response_text)
            if not data.get("detected"):
                return None
            if data.get("question") and data.get("answer"):
                return {"question": data["question"], "answer": data["answer"]}
        except json.JSONDecodeError:
            pass

        logger.warning(f"Failed to parse LLM response as JSON: {response_text[:200]}")
        return None

    @property
    def detected_questions(self) -> list[DetectedQA]:
        return self._detected_questions.copy()

    @property
    def is_analyzing(self) -> bool:
        return self._is_analyzing

    def clear(self) -> None:
        """Clear all state."""
        self._transcript_buffer.clear()
        self._detected_questions.clear()
        self._pending_text.clear()
        self._is_analyzing = False
