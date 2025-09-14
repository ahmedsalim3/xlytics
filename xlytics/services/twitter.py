import asyncio
from pathlib import Path
from typing import Dict, List

from pytwitter import Api
from pytwitter.error import PyTwitterError

from ..config.config import EnvConfig
from ..commons.logger import Logger
from ..commons.utils import safe_iter

from .helpers import (
    get_tweet_id_from_url,
    build_media_item_async,
    build_user_info,
    convert_public_metrics_to_dict,
    convert_entities_to_dict,
    convert_context_annotations_to_list,
    convert_referenced_tweets_to_list,
    convert_attachments_to_dict,
)

from .utils.file_utils import download_media_async
from .utils.decorators import retry_on_exception_async

logger = Logger()


class TwitterAPI:
    def __init__(self, env: EnvConfig, sleep_on_rate_limit: bool = True, output_name: str = None):
        logger.info(
            f"Initializing TwitterAPI with sleep_on_rate_limit: {sleep_on_rate_limit}"
        )
        self.env = env
        self.output_name = output_name or env.get("OUTPUT_NAME", "output")
        self.api = Api(
            bearer_token=self.env.get("TWITTER_BEARER_TOKEN"),
            consumer_key=self.env.get("TWITTER_API_KEY"),
            consumer_secret=self.env.get("TWITTER_API_SECRET"),
            access_token=self.env.get("TWITTER_ACCESS_TOKEN"),
            access_secret=self.env.get("TWITTER_ACCESS_TOKEN_SECRET"),
            sleep_on_rate_limit=sleep_on_rate_limit,
        )

    def get_metadata_path(self) -> Path:
        return Path(self.output_name) / "metadata.json"

    async def fetch_tweet_by_url_async(self, url: str) -> Dict:
        """Async version of fetch_tweet_by_url"""
        logger.info(f"Fetching tweet by URL asynchronously: {url}")
        try:
            tweet_id = get_tweet_id_from_url(url)
            res = self.api.get_tweet(
                tweet_id=tweet_id,
                expansions=[
                    "attachments.media_keys",
                    "author_id",
                    "referenced_tweets.id",
                ],
                tweet_fields=[
                    "created_at",
                    "public_metrics",
                    "entities",
                    "context_annotations",
                    "conversation_id",
                    "lang",
                    "possibly_sensitive",
                    "reply_settings",
                    "source",
                    "withheld",
                    "text",
                ],
                media_fields=[
                    "type",
                    "url",
                    "duration_ms",
                    "height",
                    "width",
                    "alt_text",
                    "preview_image_url",
                    "public_metrics",
                    "variants",
                ],
                user_fields=[
                    "username",
                    "verified",
                    "profile_image_url",
                    "public_metrics",
                    "description",
                    "location",
                    "created_at",
                    "protected",
                ],
            )

            tweet_data = res.data
            includes = res.includes

            # Extract media info using async helper
            media_info = []
            for i, media in enumerate(safe_iter(includes, "media")):
                media_item = await build_media_item_async(
                    media, tweet_id, i, lambda url, tid: download_media_async(url, tid, Path(self.output_name) / "media")
                )
                media_info.append(media_item)

            # Extract user info using helper
            user_info = None
            if tweet_data.author_id:
                for user in safe_iter(includes, "users"):
                    if user.id == tweet_data.author_id:
                        user_info = build_user_info(user)
                        break

            # Compile complete tweet data
            tweet_metadata = {
                "tweet_id": tweet_data.id,
                "text": tweet_data.text,
                "created_at": tweet_data.created_at,
                "lang": tweet_data.lang,
                "possibly_sensitive": tweet_data.possibly_sensitive,
                "reply_settings": tweet_data.reply_settings,
                "source": tweet_data.source,
                "public_metrics": convert_public_metrics_to_dict(tweet_data.public_metrics),
                "entities": convert_entities_to_dict(tweet_data.entities),
                "context_annotations": convert_context_annotations_to_list(tweet_data.context_annotations),
                "conversation_id": tweet_data.conversation_id,
                "author_id": tweet_data.author_id,
                "referenced_tweets": convert_referenced_tweets_to_list(tweet_data.referenced_tweets),
                "attachments": convert_attachments_to_dict(tweet_data.attachments),
                "media": media_info,
                "author": user_info,
                "url": url,
                "tweet_url": f"https://twitter.com/i/status/{tweet_data.id}",
            }

            logger.info(
                f"Fetched tweet {tweet_id} with {len(media_info)} media items asynchronously"
            )
            return tweet_metadata

        except PyTwitterError as e:
            logger.error(f"Twitter API error: {e}")
            return {}
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return {}

    @retry_on_exception_async(
        max_retries=3, delay=60, backoff=2, exceptions=(PyTwitterError,)
    )
    async def fetch_tweets_by_search_async(
        self, query: str, num_posts: int = 10
    ) -> List[Dict]:
        """Async version of fetch_tweets_by_search with better rate limit handling"""
        logger.info(
            f"Searching tweets asynchronously with query: '{query}', num_posts: {num_posts}"
        )

        assert num_posts >= 10, "num_posts must be at least 10"
        tweets_data = []
        max_request = min(num_posts, 100)

        res = self.api.search_tweets(
            query=query,
            max_results=max_request,
            expansions=["attachments.media_keys", "author_id", "referenced_tweets.id"],
            tweet_fields=[
                "created_at",
                "public_metrics",
                "entities",
                "context_annotations",
                "conversation_id",
                "lang",
                "possibly_sensitive",
                "reply_settings",
                "source",
                "withheld",
                "text",
            ],
            media_fields=[
                "type",
                "url",
                "duration_ms",
                "height",
                "width",
                "alt_text",
                "preview_image_url",
                "public_metrics",
                "variants",
            ],
            user_fields=[
                "username",
                "verified",
                "profile_image_url",
                "public_metrics",
                "description",
                "location",
                "created_at",
                "protected",
            ],
        )

        tweets = res.data
        includes = res.includes

        logger.debug(
            f"Found {len(tweets)} tweets, {len(safe_iter(includes, 'media'))} media items, {len(safe_iter(includes, 'users'))} users"
        )

        # Create lookup dictionaries using helpers
        media_lookup = {
            media.media_key: media for media in safe_iter(includes, "media")
        }
        user_lookup = {user.id: user for user in safe_iter(includes, "users")}

        # Process each tweet asynchronously
        tasks = []
        for tweet in tweets:
            task = self.process_tweet_async(tweet, media_lookup, user_lookup)
            tasks.append(task)

        # Wait for all tweet processing to complete
        if tasks:
            tweet_metadata_list = await asyncio.gather(*tasks, return_exceptions=True)
            tweets_data = [
                metadata
                for metadata in tweet_metadata_list
                if isinstance(metadata, dict)
            ]

        logger.info(f"Processed {len(tweets_data)} tweets from search asynchronously")
        return tweets_data

    async def process_tweet_async(
        self, tweet, media_lookup: dict, user_lookup: dict
    ) -> Dict:
        """Process a single tweet asynchronously"""
        logger.debug(f"Processing tweet {tweet.id} asynchronously")
        try:
            # Extract media information
            media_info = []
            if tweet.attachments and tweet.attachments.media_keys:
                media_tasks = []
                for i, media_key in enumerate(tweet.attachments.media_keys):
                    if media_key in media_lookup:
                        media = media_lookup[media_key]
                        task = build_media_item_async(
                            media, tweet.id, i, lambda url, tid: download_media_async(url, tid, Path(self.output_name) / "media")
                        )
                        media_tasks.append(task)

                # Wait for all media downloads to complete
                if media_tasks:
                    media_items = await asyncio.gather(
                        *media_tasks, return_exceptions=True
                    )
                    media_info = [
                        item for item in media_items if isinstance(item, dict)
                    ]

            # Extract user information
            user_info = None
            if tweet.author_id and tweet.author_id in user_lookup:
                user = user_lookup[tweet.author_id]
                user_info = build_user_info(user)

            # Compile tweet metadata
            tweet_metadata = {
                "tweet_id": tweet.id,
                "text": tweet.text,
                "created_at": tweet.created_at,
                "lang": tweet.lang,
                "possibly_sensitive": tweet.possibly_sensitive,
                "reply_settings": tweet.reply_settings,
                "source": tweet.source,
                "public_metrics": convert_public_metrics_to_dict(tweet.public_metrics),
                "entities": convert_entities_to_dict(tweet.entities),
                "context_annotations": convert_context_annotations_to_list(tweet.context_annotations),
                "conversation_id": tweet.conversation_id,
                "author_id": tweet.author_id,
                "referenced_tweets": convert_referenced_tweets_to_list(tweet.referenced_tweets),
                "attachments": convert_attachments_to_dict(tweet.attachments),
                "media": media_info,
                "author": user_info,
                "tweet_url": f"https://twitter.com/i/status/{tweet.id}",
            }

            logger.debug(f"Processed tweet {tweet.id}")
            return tweet_metadata

        except Exception as e:
            logger.error(f"Error processing tweet {tweet.id}: {e}")
            return {}
