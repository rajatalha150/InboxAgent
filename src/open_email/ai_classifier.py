"""Optional AI classifier using Ollama for smart email classification."""

import logging

logger = logging.getLogger(__name__)

DEFAULT_MODEL = "llama3.2:3b"
TIMEOUT = 30  # seconds

SYSTEM_PROMPT = (
    "You are an email classifier. You will be given an email and a question about it. "
    "Answer ONLY with 'yes' or 'no'. Do not explain."
)


class AIClassifier:
    """Ollama-based email classifier. Gracefully degrades if Ollama is unavailable."""

    def __init__(self, model: str = DEFAULT_MODEL):
        self.model = model
        self._available: bool | None = None
        self._client = None

    def is_available(self) -> bool:
        """Check if Ollama is reachable and cache the result."""
        if self._available is not None:
            return self._available

        try:
            import ollama
            self._client = ollama.Client()
            self._client.list()
            self._available = True
            logger.info("Ollama is available, using model: %s", self.model)
        except Exception as e:
            self._available = False
            logger.info("Ollama not available, AI rules will be skipped: %s", e)

        return self._available

    def classify(self, prompt: str, email_content: str) -> bool:
        """Send email content + prompt to Ollama and return True/False.

        Args:
            prompt: The user-defined question about the email.
            email_content: The email text to classify.

        Returns:
            True if Ollama answers 'yes', False otherwise.
        """
        if not self.is_available():
            return False

        user_message = f"Email:\n---\n{email_content}\n---\n\nQuestion: {prompt}"

        try:
            response = self._client.chat(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_message},
                ],
            )
            answer = response["message"]["content"].strip().lower()
            result = answer.startswith("yes")
            logger.debug("AI classification for prompt '%s': %s (raw: %s)", prompt, result, answer)
            return result
        except Exception as e:
            logger.warning("AI classification failed: %s", e)
            # Mark as unavailable so we don't keep trying on a broken connection
            self._available = False
            return False

    def reset(self) -> None:
        """Reset availability check (e.g., for retry after Ollama starts)."""
        self._available = None
        self._client = None
