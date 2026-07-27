"""
DesktopAI
Hybrid AI Categorizer

Uses instant rule-based matching first (milliseconds).
Falls back to local LLM ONLY for ambiguous files (seconds).
"""
import json
from pathlib import Path
from typing import Optional

from ai.ollama_client import generate_response
from core import config
from core.logger import get_logger

logger = get_logger("ai")

# Fast-path rules: Extension or filename keyword -> Category
FAST_PATH_RULES = {
    # Media & Archives (Instant)
    '.mp4': 'Videos', '.mkv': 'Videos', '.avi': 'Videos', '.mov': 'Videos',
    '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio', '.m4a': 'Audio',
    '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images', '.gif': 'Images', '.heic': 'Images',
    '.zip': 'Archives', '.rar': 'Archives', '.7z': 'Archives', '.tar': 'Archives', '.gz': 'Archives',
    
    # Programming (Instant)
    '.py': 'Programming', '.js': 'Programming', '.html': 'Programming', '.css': 'Programming',
    '.java': 'Programming', '.cpp': 'Programming', '.c': 'Programming', '.rs': 'Programming',
    '.go': 'Programming', '.json': 'Programming', '.xml': 'Programming',
    
    # Document Keywords (Instant if found in filename)
    'invoice': 'Finance', 'bill': 'Finance', 'receipt': 'Finance', 'bank': 'Finance', 'tax': 'Finance',
    'resume': 'Personal', 'cv': 'Personal', 'cover letter': 'Personal',
    'syllabus': 'Education', 'assignment': 'Education', 'homework': 'Education', 'thesis': 'Education',
    'contract': 'Legal', 'agreement': 'Legal', 'nda': 'Legal',
    'medical': 'Medical', 'prescription': 'Medical', 'health': 'Medical',
}

def fast_categorize(file_name: str, extension: str) -> Optional[dict]:
    """Attempt to categorize instantly using rules. Returns None if ambiguous."""
    ext_lower = extension.lower()
    name_lower = file_name.lower()
    
    # 1. Check exact extension match for obvious media/code/archives
    if ext_lower in FAST_PATH_RULES:
        return {
            "category": FAST_PATH_RULES[ext_lower],
            "confidence": 0.95,
            "reason": f"Fast-path rule: Extension '{ext_lower}' is definitively categorized."
        }
    
    # 2. Check for strong keywords in the filename
    for keyword, category in FAST_PATH_RULES.items():
        if not keyword.startswith('.'): # Only check string keywords here
            if keyword in name_lower:
                return {
                    "category": category,
                    "confidence": 0.85,
                    "reason": f"Fast-path rule: Filename contains keyword '{keyword}'."
                }
                
    return None # Ambiguous, needs LLM

CATEGORIZATION_PROMPT = """You are an expert AI file organization assistant. 
Analyze the provided file information and determine the most appropriate, broad semantic category.

Preferred categories: Finance, Legal, Medical, Education, Programming, Research, Images, Audio, Video, Archives, Personal, Miscellaneous.

File Name: {file_name}
Extension: {extension}
Parent Folder: {parent_folder}
Content Snippet: {content_snippet}

Respond ONLY with a valid JSON object in this exact format:
{{
  "category": "CategoryName",
  "confidence": 0.90,
  "reason": "Brief 1-sentence explanation."
}}
Do not include markdown, code blocks, or extra text. Just raw JSON.
"""

def categorize_file(
    file_name: str,
    extension: str,
    parent_folder: str,
    content_snippet: str
) -> dict:
    """Hybrid categorization: Fast rules first, LLM fallback for ambiguous files."""
    
    # Step 1: Try fast path (Takes < 1 millisecond)
    fast_result = fast_categorize(file_name, extension)
    if fast_result:
        logger.debug(f"Fast-path matched: {file_name} -> {fast_result['category']}")
        return fast_result
        
    # Step 2: Fallback to LLM for ambiguous files (Takes 1-3 seconds)
    logger.debug(f"Fast-path failed, querying LLM for: {file_name}")
    
    # Reduced snippet length to make LLM inference much faster
    max_snippet_length = 600 
    snippet = content_snippet[:max_snippet_length] if content_snippet else "No text content available."
    
    prompt = CATEGORIZATION_PROMPT.format(
        file_name=file_name,
        extension=extension,
        parent_folder=parent_folder,
        content_snippet=snippet
    )
    
    # Use the ultra-fast 1B model for this specific task
    model_name = getattr(config, 'OLLAMA_MODEL_FAST', 'llama3.2:1b')
    response = generate_response(prompt, model=model_name, timeout=45)
    
    if not response:
        return {
            "category": "Miscellaneous",
            "confidence": 0.1,
            "reason": "LLM request failed or timed out."
        }
        
    try:
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.endswith("```"):
            response = response[:-3]
            
        result = json.loads(response.strip())
        return {
            "category": str(result.get("category", "Miscellaneous")).strip().title(),
            "confidence": float(result.get("confidence", 0.5)),
            "reason": str(result.get("reason", "LLM categorized based on content."))
        }
    except (json.JSONDecodeError, ValueError) as e:
        logger.warning(f"Failed to parse AI JSON for {file_name}: {e}")
        return {
            "category": "Miscellaneous",
            "confidence": 0.1,
            "reason": "AI response parsing failed."
        }