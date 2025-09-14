import re
from typing import Callable, Dict, Any

from ..commons.logger import Logger

logger = Logger()

class DictAsMember(dict):
    """Dict as member trick."""

    def __getattr__(self, name):
        value = self[name]
        if isinstance(value, dict):
            value = DictAsMember(value)
        return value


def convert_public_metrics_to_dict(metrics) -> Dict[str, Any]:
    """Convert Twitter public metrics object to dictionary"""
    if not metrics:
        return {}
    
    # Handle different types of public metrics objects
    if hasattr(metrics, '__dict__'):
        # Convert object attributes to dict
        return {k: v for k, v in metrics.__dict__.items() if not k.startswith('_')}
    elif hasattr(metrics, 'like_count'):
        # Handle TweetPublicMetrics - based on actual pytwitter model
        return {
            'like_count': getattr(metrics, 'like_count', 0),
            'retweet_count': getattr(metrics, 'retweet_count', 0),
            'reply_count': getattr(metrics, 'reply_count', 0),
            'quote_count': getattr(metrics, 'quote_count', 0),
            'bookmark_count': getattr(metrics, 'bookmark_count', 0),
            'impression_count': getattr(metrics, 'impression_count', 0),
        }
    elif hasattr(metrics, 'followers_count'):
        # Handle User PublicMetrics - based on actual pytwitter model
        return {
            'followers_count': getattr(metrics, 'followers_count', 0),
            'following_count': getattr(metrics, 'following_count', 0),
            'tweet_count': getattr(metrics, 'tweet_count', 0),
            'listed_count': getattr(metrics, 'listed_count', 0),
        }
    elif hasattr(metrics, 'view_count'):
        # Handle MediaPublicMetrics - based on actual pytwitter model
        return {
            'view_count': getattr(metrics, 'view_count', 0),
        }
    else:
        # Fallback: try to convert to dict if possible
        try:
            return dict(metrics) if hasattr(metrics, '__iter__') else {}
        except:
            return {}


def convert_entities_to_dict(entities) -> Dict[str, Any]:
    """Convert Twitter entities object to dictionary"""
    if not entities:
        return {}
    
    result = {}
    
    # Handle different entity types based on actual TweetEntities structure
    entity_types = ['annotations', 'cashtags', 'hashtags', 'mentions', 'urls']
    for entity_type in entity_types:
        if hasattr(entities, entity_type):
            entity_list = getattr(entities, entity_type, [])
            if entity_list:
                result[entity_type] = []
                for entity in entity_list:
                    if hasattr(entity, '__dict__'):
                        entity_dict = {k: v for k, v in entity.__dict__.items() if not k.startswith('_')}
                        result[entity_type].append(entity_dict)
                    else:
                        result[entity_type].append(str(entity))
    
    return result


def convert_context_annotations_to_list(annotations) -> list:
    """Convert Twitter context annotations to list of dictionaries"""
    if not annotations:
        return []
    
    result = []
    for annotation in annotations:
        if hasattr(annotation, '__dict__'):
            annotation_dict = {}
            # Handle domain object
            if hasattr(annotation, 'domain') and annotation.domain:
                if hasattr(annotation.domain, '__dict__'):
                    domain_dict = {k: v for k, v in annotation.domain.__dict__.items() if not k.startswith('_')}
                    annotation_dict['domain'] = domain_dict
                else:
                    annotation_dict['domain'] = str(annotation.domain)
            else:
                annotation_dict['domain'] = None
            
            # Handle entity object
            if hasattr(annotation, 'entity') and annotation.entity:
                if hasattr(annotation.entity, '__dict__'):
                    entity_dict = {k: v for k, v in annotation.entity.__dict__.items() if not k.startswith('_')}
                    annotation_dict['entity'] = entity_dict
                else:
                    annotation_dict['entity'] = str(annotation.entity)
            else:
                annotation_dict['entity'] = None
            
            result.append(annotation_dict)
        else:
            result.append(str(annotation))
    
    return result


def convert_referenced_tweets_to_list(referenced_tweets) -> list:
    """Convert Twitter referenced tweets to list of dictionaries"""
    if not referenced_tweets:
        return []
    
    result = []
    for ref_tweet in referenced_tweets:
        if hasattr(ref_tweet, '__dict__'):
            # Handle TweetReferencedTweet structure
            ref_dict = {
                'type': getattr(ref_tweet, 'type', None),
                'id': getattr(ref_tweet, 'id', None),
            }
            result.append(ref_dict)
        else:
            result.append(str(ref_tweet))
    
    return result


def convert_attachments_to_dict(attachments) -> Dict[str, Any]:
    """Convert Twitter attachments object to dictionary"""
    if not attachments:
        return {}
    
    result = {}
    # Handle TweetAttachments structure
    if hasattr(attachments, 'media_keys'):
        result['media_keys'] = list(attachments.media_keys) if attachments.media_keys else []
    if hasattr(attachments, 'poll_ids'):
        result['poll_ids'] = list(attachments.poll_ids) if attachments.poll_ids else []
    if hasattr(attachments, 'media_source_tweet_id'):
        result['media_source_tweet_id'] = list(attachments.media_source_tweet_id) if attachments.media_source_tweet_id else []
    
    return result


def convert_media_variants_to_list(variants) -> list:
    """Convert Twitter media variants to list of dictionaries"""
    if not variants:
        return []
    
    result = []
    for variant in variants:
        if hasattr(variant, '__dict__'):
            # Handle MediaVariant structure
            variant_dict = {
                'bit_rate': getattr(variant, 'bit_rate', None),
                'content_type': getattr(variant, 'content_type', None),
                'url': getattr(variant, 'url', None),
            }
            result.append(variant_dict)
        else:
            result.append(str(variant))
    
    return result


def get_tweet_id_from_url(url: str) -> str:
    """
    Get tweet ID from Twitter URL.
    Alternative and simpler method is just to
    split the url by '/' and get the last element.

    for example:

    url: https://twitter.com/elonmusk/status/1460062031084761090
    res= url.split('/')[-1]
    res: 1460062031084761090
    """
    logger.debug(f"Extracting tweet ID from URL: {url}")

    # handle various Twitter URL formats
    patterns = [
        r"twitter\.com/\w+/status/(\d+)",
        r"twitter\.com/i/status/(\d+)",
        r"x\.com/\w+/status/(\d+)",
        r"x\.com/i/status/(\d+)",
    ]

    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            tweet_id = match.group(1)
            logger.debug(f"Extracted tweet ID: {tweet_id}")
            return tweet_id

    msg = f"Could not extract tweet ID from URL: {url}"
    logger.error(msg)
    raise ValueError(msg)


def build_media_item(
    media, tweet_id: str, index: int, download_media_fn: Callable
) -> dict:
    """Build a media item dictionary with optional download"""
    logger.debug(f"Building media item for tweet {tweet_id}, index {index}")

    item = {
        "media_key": media.media_key,
        "type": media.type,
        "url": media.url,
        "duration_ms": media.duration_ms,
        "height": media.height,
        "width": media.width,
        "alt_text": media.alt_text,
        "preview_image_url": media.preview_image_url,
        "public_metrics": convert_public_metrics_to_dict(media.public_metrics),
        "variants": convert_media_variants_to_list(media.variants),
    }

    # Download media if URL is available
    download_url = None
    if media.url:
        download_url = media.url
    elif media.variants:
        # Try to find the best quality video URL from variants
        for variant in media.variants:
            if (
                hasattr(variant, "url")
                and variant.url
                and "video/mp4" in getattr(variant, "content_type", "")
            ):
                download_url = variant.url
                break
        # If no video URL found, try any URL from variants
        if not download_url:
            for variant in media.variants:
                if hasattr(variant, "url") and variant.url:
                    download_url = variant.url
                    break

    if download_url:
        logger.debug(f"Downloading media for tweet {tweet_id} from {download_url}")
        local_path = download_media_fn(download_url, tweet_id, index)
        if local_path:
            item["local_path"] = str(local_path)
            item["download_url"] = download_url
        else:
            logger.warning(f"Failed to download media for tweet {tweet_id}")
    else:
        logger.debug(f"No URL available for media in tweet {tweet_id}")

    return item


async def build_media_item_async(
    media, tweet_id: str, index: int, download_media_fn: Callable
) -> dict:
    """Async version of build_media_item"""
    logger.debug(f"Building async media item for tweet {tweet_id}, index {index}")

    item = {
        "media_key": media.media_key,
        "type": media.type,
        "url": media.url,
        "duration_ms": media.duration_ms,
        "height": media.height,
        "width": media.width,
        "alt_text": media.alt_text,
        "preview_image_url": media.preview_image_url,
        "public_metrics": convert_public_metrics_to_dict(media.public_metrics),
        "variants": convert_media_variants_to_list(media.variants),
    }

    # Download media if URL is available
    download_url = None
    if media.url:
        download_url = media.url
    elif media.variants:
        # Try to find the best quality video URL from variants
        for variant in media.variants:
            if (
                hasattr(variant, "url")
                and variant.url
                and "video/mp4" in getattr(variant, "content_type", "")
            ):
                download_url = variant.url
                break
        # If no video URL found, try any URL from variants
        if not download_url:
            for variant in media.variants:
                if hasattr(variant, "url") and variant.url:
                    download_url = variant.url
                    break

    if download_url:
        logger.debug(
            f"Downloading media async for tweet {tweet_id} from {download_url}"
        )
        local_path = await download_media_fn(download_url, tweet_id)
        if local_path:
            item["local_path"] = str(local_path)
            item["download_url"] = download_url
        else:
            logger.warning(f"Failed to download media async for tweet {tweet_id}")
    else:
        logger.debug(f"No URL available for async media in tweet {tweet_id}")

    return item


def build_user_info(user) -> dict:
    """Build a user information dictionary"""
    logger.debug(f"Building user info for user {user.username}")

    return {
        "id": user.id,
        "username": user.username,
        "verified": user.verified,
        "profile_image_url": user.profile_image_url,
        "public_metrics": convert_public_metrics_to_dict(user.public_metrics),
        "description": user.description,
        "location": user.location,
        "created_at": user.created_at,
        "protected": user.protected,
    }
