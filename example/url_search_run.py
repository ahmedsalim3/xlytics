import argparse
import asyncio

from xlytics.services import TwitterAPI, save_metadata
from xlytics.config.config import EnvConfig

env = EnvConfig()


async def search(twitter_api, query, num_posts):
    tweets = await twitter_api.fetch_tweets_by_search_async(query, num_posts=num_posts)
    save_metadata(tweets, twitter_api.get_metadata_path())
    return tweets


async def url(twitter_api, url):
    tweet_data = await twitter_api.fetch_tweet_by_url_async(url)
    save_metadata(tweet_data, twitter_api.get_metadata_path())
    return tweet_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Xlytics Twitter Analytics Tool")
    parser.add_argument("--mode", type=str, default="search", choices=["search", "url"], 
                       help="Mode: 'search' for searching tweets or 'url' for fetching by URL")
    parser.add_argument("--output", type=str, default=None, 
                       help="Output directory name (default: from config or 'output')")
    parser.add_argument("--num_posts", type=int, default=10, 
                       help="Number of posts to fetch (for search mode, minimum 10)")
    parser.add_argument("query_or_url", nargs="?", 
                       help="Search query (for search mode) or tweet URL (for url mode)")
    
    args = parser.parse_args()

    if not args.query_or_url:
        parser.error("query_or_url is required")
    
    if args.mode == "search" and args.num_posts < 10:
        parser.error("num_posts must be at least 10 for search mode")

    twitter_api = TwitterAPI(env, sleep_on_rate_limit=True, output_name=args.output)

    if args.mode == "search":
        print(f"Searching for tweets with query: '{args.query_or_url}' (num_posts: {args.num_posts})")
        results = asyncio.run(search(twitter_api, args.query_or_url, args.num_posts))
        print(f"Found {len(results)} tweets")
        print(results)

    elif args.mode == "url":
        print(f"Fetching tweet from URL: {args.query_or_url}")
        result = asyncio.run(url(twitter_api, args.query_or_url))
        print("Tweet fetched successfully:")
        print(result)
