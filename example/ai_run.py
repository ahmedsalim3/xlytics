import json
import asyncio
import sys
import argparse
from pathlib import Path

from xlytics.llms.pipeline import VisionPipeline
from xlytics.llms.local_lang import LocalLLM
from xlytics.config.config import ModelConfig
from xlytics.llms.prompts import (
    build_language_user_prompt,
    build_vision_user_prompt,
    build_final_user_prompt,
    get_language_prompt,
    get_vision_prompt
)


def load_tweet_data(metadata_path):
    """Load tweet data from metadata file, handling both list and single object formats"""
    with open(metadata_path, 'r') as f:
        data = json.load(f)
    
    # Handle both formats: list of tweets (search output) or single tweet (URL output)
    if isinstance(data, list):
        return data
    elif isinstance(data, dict):
        return [data]  # Convert single tweet to list format
    else:
        raise ValueError(f"Unexpected data format in {metadata_path}")


def analyze_media(tweet_data, media_item, max_frames=5):
    """Analyze a single media item using vision model"""
    config = ModelConfig()
    vision = VisionPipeline(config, max_frames=max_frames)
    
    # Fix path resolution - handle both absolute and relative paths
    local_path = media_item["local_path"]
    if not Path(local_path).exists():
        # Try relative path from example directory
        relative_path = Path("search_output") / Path(local_path).name
        if relative_path.exists():
            local_path = str(relative_path)
        else:
            # Try url_output directory
            relative_path = Path("url_output") / Path(local_path).name
            if relative_path.exists():
                local_path = str(relative_path)
    
    print(f"Using media path: {local_path}")
    
    # Get vision prompt
    result = vision.analyze(
        image_path = Path(local_path),
        conf=float(config.get("YOLO_CONFIDENCE_THRESHOLD")),
        prompt=build_vision_user_prompt(tweet_data, media_item),
        system_prompt=get_vision_prompt(),
    )
    
    return result


def analyze_text(tweet_data):
    """Analyze tweet text using language model"""
    config = ModelConfig()
    
    # Get language prompt
    language_prompt = build_language_user_prompt(tweet_data)
    language_system_prompt = get_language_prompt()
    
    # Get model name
    model_name = config.get("OLLAMA_MODEL")
    # model_name = models.get("GROQ_MODEL")
    # OR SEE AVAILABLE MODELS BY RUNNING
    # print(config.models_list())

    lang = LocalLLM(config, model_name)
    result = lang.generate(
        prompt=language_prompt,
        system_prompt=language_system_prompt,
        max_tokens=1000,
        temperature=0.7,
    )
    
    import json
    import re
    
    # Try to find and parse JSON in the response
    parsed_result = None
    
    # First, try to find JSON object in the response
    json_patterns = [
        r'\{[^{}]*(?:\{[^{}]*\}[^{}]*)*\}',  # Simple nested JSON
        r'\{.*?\}',  # Any JSON-like structure
    ]
    
    for pattern in json_patterns:
        json_matches = re.findall(pattern, result, re.DOTALL)
        for json_str in json_matches:
            try:
                parsed_result = json.loads(json_str)
                break
            except json.JSONDecodeError:
                continue
        if parsed_result:
            break
    
    # If no valid JSON found, create a default structure
    if not parsed_result:
        parsed_result = {
            "risk_level": "UNKNOWN",
            "content_type": "unclear",
            "fraud_indicators": [],
            "security_threats": [],
            "linguistic_analysis": {"tone": "unknown", "sentiment": "unknown", "red_flags": []},
            "confidence_score": 0,
            "recommendations": [],
            "contextual_notes": result
        }
    
    return parsed_result


def save_analysis_results(tweet_data, vision_results, language_result, final_result, output_dir=Path("output")):

    output_dir.mkdir(exist_ok=True)
    results = {
        "tweet_data": tweet_data,
        "vision_results": vision_results,
        "language_result": language_result,
        "final_result": final_result
    }
    
    with open(output_dir / "analysis_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)
    
    print(f"Analysis results saved to: {output_dir / 'analysis_results.json'}")


def main():
    """Main function to run the AI analysis pipeline"""
    parser = argparse.ArgumentParser(description="Run AI analysis on tweet data")
    parser.add_argument("--max-frames", type=int, default=5, 
                       help="Maximum number of frames to extract from videos (default: 5)")
    parser.add_argument("--metadata", type=str, 
                       help="Path to specific metadata file (optional)")
    args = parser.parse_args()
    
    print("Loading tweet data from metadata file...")
    
    # Determine which metadata file to use
    if args.metadata:
        metadata_path = Path(args.metadata)
        if not metadata_path.exists():
            print(f"Error: Specified metadata file not found: {metadata_path}")
            sys.exit(1)
        print(f"Using specified metadata: {metadata_path}")
    else:
        search_metadata = Path("search_output/metadasta.json")
        url_metadata = Path("url_output/metadata.json")
        
        if search_metadata.exists():
            metadata_path = search_metadata
            print(f"Using search output metadata: {metadata_path}")
        elif url_metadata.exists():
            metadata_path = url_metadata
            print(f"Using URL output metadata: {metadata_path}")
        else:
            print("Error: No metadata file found. Please run the search or URL script first.")
            print("Expected files:")
            print(f"  - {search_metadata.absolute()}")
            print(f"  - {url_metadata.absolute()}")
            sys.exit(1)
    
    # Load tweet data (this is now a list of tweets)
    tweets_data = load_tweet_data(metadata_path)
    print(f"Loaded {len(tweets_data)} tweets from {metadata_path}")
    print(f"Max frames for video analysis: {args.max_frames}")
    
    # Find a tweet with media, or use the first tweet if none have media
    tweet_data = None
    for tweet in tweets_data:
        if tweet.get("media") and len(tweet["media"]) > 0:
            tweet_data = tweet
            print(f"Found tweet with media: {tweet_data.get('text', '')[:100]}...")
            break
    
    if not tweet_data:
        # If no tweet with media found, use the first tweet
        tweet_data = tweets_data[0] if tweets_data else {}
        print(f"Using first tweet (no media): {tweet_data.get('text', '')[:100]}...")
    
    # Analyze media (if any)
    vision_results = []
    media_items = tweet_data.get("media", [])
    
    if media_items:
        print(f"Found {len(media_items)} media items to analyze...")
        for i, media_item in enumerate(media_items):
            print(f"Analyzing media {i+1}/{len(media_items)}: {media_item.get('type', 'unknown')}")
            vision_result = analyze_media(tweet_data, media_item, max_frames=args.max_frames)
            if vision_result:
                vision_results.append(vision_result)
                print(f"✓ Media {i+1} analysis complete")
            else:
                print(f"✗ Media {i+1} analysis failed")
    else:
        print("No media items found")
    
    # Analyze text
    print("Analyzing tweet text...")
    language_result = analyze_text(tweet_data)
    print("✓ Text analysis complete")
    
    # Generate final combined analysis
    print("Generating final combined analysis...")
    final_prompt = build_final_user_prompt(tweet_data, vision_results, language_result)
    
    # Use language model for final analysis
    config = ModelConfig()
    model_name = config.get("OLLAMA_MODEL", "llama3.1:8b")
    lang = LocalLLM(config, model_name)
    
    final_result = lang.generate(
        prompt=final_prompt,
        system_prompt=get_language_prompt(),
        max_tokens=1500,
        temperature=0.7,
    )
    
    print("✓ Final analysis complete")
    
    # Save results
    save_analysis_results(tweet_data, vision_results, language_result, final_result)
    
    # Print summary
    print("\n" + "="*50)
    print("ANALYSIS COMPLETE")
    print("="*50)
    print(f"Tweet: {tweet_data.get('text', '')[:100]}...")
    print(f"Media analyzed: {len(vision_results)}")
    print(f"Language analysis: {len(language_result)} characters")
    print(f"Final analysis: {len(final_result)} characters")
    print("="*50)


if __name__ == "__main__":
    main()
    