import json
from pathlib import Path
from typing import Dict, List, Union
from urllib.parse import urlparse

import aiohttp
import requests

from ...commons.logger import Logger

logger = Logger()


def download_media(
    media_url: str, tweet_id: str, output: Path = None
) -> Path:
    """Download media file from URL and save under media/tweet_id/ folder with original filename."""
    try:
        logger.info(f"Downloading media for tweet {tweet_id} from {media_url}")

        if output is None:
            output = Path("output/media")

        # Ensure output directory exists
        tweet_folder = output / tweet_id
        tweet_folder.mkdir(parents=True, exist_ok=True)

        # get filename from media_url
        filename = Path(urlparse(media_url).path).name
        file_path = tweet_folder / filename

        res = requests.get(media_url, stream=True)
        res.raise_for_status()

        with open(file_path, "wb") as f:
            for chunk in res.iter_content(chunk_size=8192):
                f.write(chunk)

        logger.info(f"Downloaded media to {file_path}")
        return file_path.resolve()

    except Exception as e:
        logger.error(f"Error downloading media from {media_url}: {e}")
        return None


async def download_media_async(
    media_url: str, tweet_id: str, output: Path = None
) -> Path:
    """Async version of download_media - saves files the same way"""
    try:
        logger.info(f"Downloading media async for tweet {tweet_id} from {media_url}")

        if output is None:
            output = Path("output/media")

        # Ensure output directory exists
        tweet_folder = output / tweet_id
        tweet_folder.mkdir(parents=True, exist_ok=True)

        # get filename from media_url
        filename = Path(urlparse(media_url).path).name
        file_path = tweet_folder / filename

        async with aiohttp.ClientSession() as session:
            async with session.get(media_url) as response:
                response.raise_for_status()

                with open(file_path, "wb") as f:
                    async for chunk in response.content.iter_chunked(8192):
                        f.write(chunk)

        logger.info(f"Downloaded media async to {file_path}")
        return file_path.resolve()

    except Exception as e:
        logger.error(f"Error downloading media async from {media_url}: {e}")
        return None


def save_metadata(
    data: Union[Dict, List[Dict]],
    output: Union[str, Path] = None,
) -> Path:
    """Save metadata to JSON file"""
    try:
        if output is None:
            output = Path("output/metadata.json")
        
        # Convert string to Path if needed
        if isinstance(output, str):
            output = Path(output)

        # Ensure the output directory exists
        output.parent.mkdir(parents=True, exist_ok=True)

        with open(output, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, default=str)

        logger.info(f"Successfully saved metadata to {output}")
        return output

    except Exception as e:
        logger.error(f"Error saving metadata to {output}: {e}")
        return None
