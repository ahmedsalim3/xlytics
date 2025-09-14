
from typing import Dict, Any, List


class LanguagePrompt:
    """
    A very simple language analysis prompt.
    """

    SYSTEM_PROMPT = """
    You are a simple language model.
    Task: Read the input text and explain what it is about in plain language.
    """


class VisionPrompt:
    """
    A very simple vision analysis prompt.
    """

    SYSTEM_PROMPT = """
    You are a simple vision model.
    Task: Look at the image and explain what is shown in a clear and simple way.
    """


def get_language_prompt() -> str:
    """Get the system prompt for text analysis."""
    return LanguagePrompt.SYSTEM_PROMPT.strip()


def get_vision_prompt() -> str:
    """Get the system prompt for image analysis."""
    return VisionPrompt.SYSTEM_PROMPT.strip()


def build_language_user_prompt(tweet_data: Dict) -> str:
    """
    Builds a simple user prompt for analyzing tweet text.
    """
    tweet_text = tweet_data.get("text", "").strip()
    author = tweet_data.get("author", {})
    
    prompt = f"""Please analyze this tweet and tell me what it's about:

Tweet: "{tweet_text}"

Author: @{author.get("username", "unknown")}
Verified: {author.get("verified", False)}

Please provide a simple explanation of what this tweet is about."""
    
    return prompt


def build_vision_user_prompt(tweet_data: Dict, media_item: Dict) -> str:
    """
    Builds a simple user prompt for analyzing media content.
    """
    tweet_text = tweet_data.get("text", "").strip()
    author = tweet_data.get("author", {})
    image_path = media_item.get("local_path", "N/A")
    media_type = media_item.get("type", "unknown")
    
    prompt = f"""Please look at this {media_type} and tell me what you see:

Media file: {image_path}
Tweet context: "{tweet_text}"
Author: @{author.get("username", "unknown")}

Please describe what you see in the image/video in simple terms."""
    
    return prompt


def build_final_user_prompt(tweet_data: Dict, 
                            vision_results: List[Dict], 
                            language_result: Dict) -> str:
    """
    Builds a simple final prompt combining all analysis results.
    """
    tweet_text = tweet_data.get("text", "").strip()
    author = tweet_data.get("author", {})
    
    # Simple vision summary
    vision_summary = ""
    if vision_results:
        descriptions = [result.get("scene_description", "No description") for result in vision_results]
        vision_summary = f"Media analysis: {'; '.join(descriptions)}"
    else:
        vision_summary = "No media found"
    
    # Simple language summary
    language_summary = str(language_result) if language_result else "No text analysis"
    
    prompt = f"""Please provide a simple summary of this tweet analysis:

Tweet: "{tweet_text}"
Author: @{author.get("username", "unknown")}

Text Analysis: {language_summary}
{vision_summary}

Please give me a brief, simple summary of what this tweet is about and any notable findings."""
    
    return prompt
