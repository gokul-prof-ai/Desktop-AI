"""
DesktopAI
Hybrid AI Categorizer (Enhanced with Regex Fallback)
"""
import json
import re
from pathlib import Path
from typing import Optional

from ai.ollama_client import generate_response
from core import config
from core.logger import get_logger

logger = get_logger("ai")

FAST_PATH_RULES = {
    '.mp4': 'Videos', '.mkv': 'Videos', '.avi': 'Videos', '.mov': 'Videos', '.wmv': 'Videos',
    '.mp3': 'Audio', '.wav': 'Audio', '.flac': 'Audio', '.m4a': 'Audio', '.aac': 'Audio',
    '.jpg': 'Images', '.jpeg': 'Images', '.png': 'Images', '.gif': 'Images', '.heic': 'Images', '.webp': 'Images',
    '.zip': 'Archives', '.rar': 'Archives', '.7z': 'Archives', '.tar': 'Archives', '.gz': 'Archives',
    '.py': 'Programming', '.js': 'Programming', '.html': 'Programming', '.css': 'Programming',
    '.java': 'Programming', '.cpp': 'Programming', '.c': 'Programming', '.rs': 'Programming',
    '.go': 'Programming', '.json': 'Programming', '.xml': 'Programming', '.sql': 'Programming',
    'invoice': 'Finance', 'bill': 'Finance', 'receipt': 'Finance', 'bank': 'Finance', 'tax': 'Finance', 'gst': 'Finance',
    'resume': 'Personal', 'cv': 'Personal', 'cover letter': 'Personal', 'passport': 'Personal', 'aadhar': 'Personal', 'pan': 'Personal',
    'syllabus': 'Education', 'assignment': 'Education', 'homework': 'Education', 'thesis': 'Education', 'notes': 'Education',
    'contract': 'Legal', 'agreement': 'Legal', 'nda': 'Legal', 'terms': 'Legal',
    'medical': 'Medical', 'prescription': 'Medical', 'health': 'Medical', 'report': 'Medical',
}

def fast_categorize(file_name: str, extension: str) -> Optional[dict]:
    ext_lower = extension.lower()
    name_lower = file_name.lower()
    
    if ext_lower in FAST_PATH_RULES:
        return {"category": FAST_PATH_RULES[ext_lower], "confidence": 0.95, "reason": f"Fast-path: Extension '{ext_lower}'."}
    
    for keyword, category in FAST_PATH_RULES.items():
        if not keyword.startswith('.') and keyword in name_lower:
            return {"category": category, "confidence": 0.85, "reason": f"Fast-path: Keyword '{keyword}'."}
    return None

CATEGORIZATION_PROMPT = """You are an expert AI file organizer. Determine the broad semantic category.
Categories: Finance, Legal, Medical, Education, Programming, Research, Images, Audio, Video, Archives, Personal, Miscellaneous.
File Name: {file_name} | Ext: {extension} | Folder: {parent_folder} | Snippet: {content_snippet}
Respond ONLY with raw JSON: {{"category": "Name", "confidence": 0.9, "reason": "Why"}}. No markdown."""

def categorize_file(file_name: str, extension: str, parent_folder: str, content_snippet: str) -> dict:
    fast_result = fast_categorize(file_name, extension)
    if fast_result:
        return fast_result
        
    snippet = content_snippet[:600] if content_snippet else "No text."
    prompt = CATEGORIZATION_PROMPT.format(file_name=file_name, extension=extension, parent_folder=parent_folder, content_snippet=snippet)
    
    model_name = getattr(config, 'OLLAMA_MODEL_FAST', 'llama3.2:1b')
    response = generate_response(prompt, model=model_name, timeout=45)
    
    if not response:
        return {"category": "Miscellaneous", "confidence": 0.1, "reason": "LLM failed/timed out."}
        
    # 1. Try standard JSON parsing
    try:
        clean_response = response.strip().replace("```json", "").replace("```", "")
        result = json.loads(clean_response)
        return {
            "category": str(result.get("category", "Miscellaneous")).strip().title(),
            "confidence": float(result.get("confidence", 0.5)),
            "reason": str(result.get("reason", "LLM categorized."))
        }
    except (json.JSONDecodeError, ValueError):
        pass # Fallback to regex

    # 2. Regex Fallback (If AI forgot JSON formatting)
    category_match = re.search(r'"category"\s*:\s*"([^"]+)"', response, re.IGNORECASE)
    if category_match:
        return {
            "category": category_match.group(1).strip().title(),
            "confidence": 0.6,
            "reason": "Extracted via regex fallback (AI formatting was messy)."
        }
        
    return {"category": "Miscellaneous", "confidence": 0.1, "reason": "AI response unparseable."}