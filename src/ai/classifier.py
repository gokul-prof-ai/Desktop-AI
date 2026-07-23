"""
DesktopAI
File Classifier

Uses the local Ollama LLM to assign a short category label to a
file based on its extracted text content (e.g. "Resume", "Invoice",
"Contract", "Source Code", "Meeting Notes").
"""

from ai.ollama_client import generate_response
from core import config
from core.logger import get_logger

logger = get_logger("ai")

CLASSIFICATION_PROMPT_TEMPLATE = (
    "You are a file classification assistant. Read the text below and "
    "respond with ONLY a short category label (1-3 words) describing "
    "what kind of document this is (for example: Resume, Invoice, "
    "Contract, Meeting Notes, Source Code, Receipt, Letter, Report). "
    "Do not add any explanation, punctuation, or extra text.\n\n"
    "Text:\n{text}\n\nCategory:"
)


def classify_file(text: str) -> str | None:
    """
    Ask the local AI model to categorize a file based on its text.

    Args:
        text (str):
            The extracted text content of a file (from a PDF, DOCX,
            Excel, or OCR reader).

    Returns:
        str | None:
            A short category label (e.g. "Invoice"), or None if the
            text is empty or the AI is unavailable.
    """

    if not text or not text.strip():
        logger.info("No text provided for classification; skipping.")
        return None

    truncated_text = text[: config.CLASSIFIER_MAX_TEXT_LENGTH]
    prompt = CLASSIFICATION_PROMPT_TEMPLATE.format(text=truncated_text)

    category = generate_response(prompt)

    if category is None:
        logger.warning("Classification unavailable (AI did not respond).")
        return None

    # Keep the label short and clean, in case the model adds
    # unexpected punctuation or line breaks despite instructions.
    category = category.strip().splitlines()[0].strip(" .\"'")

    logger.info("Classified file as: %s", category)

    return category