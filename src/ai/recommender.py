"""
DesktopAI
File Recommender

Uses the local Ollama LLM to suggest an organizational action for a
file (e.g. a suggested destination folder), based on its name,
classified category, and content. This produces a *suggestion*
only — DesktopAI never moves or renames files on its own; that is
the Organizer module's job, later, with user approval.
"""

from ai.ollama_client import generate_response
from core.logger import get_logger

logger = get_logger("ai")

RECOMMENDATION_PROMPT_TEMPLATE = (
    "You are a file organization assistant. Based on the information "
    "below, suggest a single short destination folder path where this "
    "file should be organized (for example: Documents/Invoices, "
    "Work/Contracts, Personal/Photos). Respond with ONLY the folder "
    "path, nothing else.\n\n"
    "File name: {file_name}\n"
    "Category: {category}\n"
    "Content preview: {text_preview}\n\n"
    "Suggested folder:"
)

MAX_TEXT_PREVIEW_LENGTH = 500


def recommend_action(file_name: str, category: str | None = None, text: str = "") -> str | None:
    """
    Ask the local AI model to suggest an organizational action
    (a destination folder) for a file.

    Args:
        file_name (str):
            The file's name, e.g. "invoice_march.pdf".
        category (str | None):
            An optional classification label from classify_file(),
            e.g. "Invoice". Improves the recommendation if available.
        text (str):
            Optional extracted text content, used as extra context.

    Returns:
        str | None:
            A suggested destination folder path (e.g.
            "Documents/Invoices"), or None if no file name was
            given or the AI is unavailable. This is a suggestion
            only — no file is moved by this function.
    """

    if not file_name or not file_name.strip():
        logger.info("No file name provided for recommendation; skipping.")
        return None

    text_preview = text[:MAX_TEXT_PREVIEW_LENGTH] if text else "(no content available)"
    category_display = category if category else "(unknown)"

    prompt = RECOMMENDATION_PROMPT_TEMPLATE.format(
        file_name=file_name,
        category=category_display,
        text_preview=text_preview,
    )

    recommendation = generate_response(prompt)

    if recommendation is None:
        logger.warning("Recommendation unavailable (AI did not respond).")
        return None

    # Keep it to a single clean line/path, in case the model adds
    # extra explanation despite instructions.
    recommendation = recommendation.strip().splitlines()[0].strip(" .\"'")

    logger.info("Recommended action for %s: %s", file_name, recommendation)

    return recommendation