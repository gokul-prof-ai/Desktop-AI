"""
DesktopAI
File Summarizer

Uses the local Ollama LLM to produce a short, human-readable
summary of a file's extracted text content.
"""

from ai.ollama_client import generate_response
from core import config
from core.logger import get_logger

logger = get_logger("ai")

SUMMARY_PROMPT_TEMPLATE = (
    "You are a document summarization assistant. Read the text below "
    "and write a concise summary in 1-3 sentences. Focus on the key "
    "facts, purpose, or content of the document. Do not add any "
    "preamble like 'Here is a summary' — just give the summary itself.\n\n"
    "Text:\n{text}\n\nSummary:"
)


def summarize_file(text: str) -> str | None:
    """
    Ask the local AI model to summarize a file's text content.

    Args:
        text (str):
            The extracted text content of a file (from a PDF, DOCX,
            Excel, or OCR reader).

    Returns:
        str | None:
            A short summary (1-3 sentences), or None if the text is
            empty or the AI is unavailable.
    """

    if not text or not text.strip():
        logger.info("No text provided for summarization; skipping.")
        return None

    truncated_text = text[: config.SUMMARIZER_MAX_TEXT_LENGTH]
    prompt = SUMMARY_PROMPT_TEMPLATE.format(text=truncated_text)

    summary = generate_response(prompt)

    if summary is None:
        logger.warning("Summarization unavailable (AI did not respond).")
        return None

    summary = summary.strip()

    logger.info("Summarized file: %d character(s) -> %d character(s)", len(text), len(summary))

    return summary