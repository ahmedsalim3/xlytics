import argparse
import asyncio

from xlytics.services import TwitterAPI, save_metadata
from xlytics.config.config import EnvConfig

env = EnvConfig()


async def search(twitter_api):
    query = "Crypto"
    tweets = await twitter_api.fetch_tweets_by_search_async(query, num_posts=10)
    save_metadata(tweets, twitter_api.get_metadata_path())
    return tweets


async def url(twitter_api):
    # url = "https://x.com/LegitTargets/status/1942901556212322343"
    # url = "https://x.com/DrLoupis__/status/1942987721431040324"
    # url = "https://x.com/politvidchannel/status/1942697005584900393"
    url = "https://x.com/StokeyyG2/status/1944517074384253256"
    tweet_data = await twitter_api.fetch_tweet_by_url_async(url)
    save_metadata(tweet_data, twitter_api.get_metadata_path())
    return tweet_data

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--mode", type=str, default="search", choices=["search", "url"])
    parser.add_argument("--output", type=str, default=None, help="Output directory name (default: from config or 'output')")
    args = parser.parse_args()

    twitter_api = TwitterAPI(env, sleep_on_rate_limit=True, output_name=args.output)

    if args.mode == "search":
        results = asyncio.run(search(twitter_api))
        print(results)

    elif args.mode == "url":
        result = asyncio.run(url(twitter_api))
        print(result)
