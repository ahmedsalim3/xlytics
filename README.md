# Xlytics

A powerful Python library for Twitter/X analytics and data summarization

## Features

- **Async Twitter API Integration**: Fetch tweets by search query or URL
- **Media Download**: Automatically download images and videos from tweets
- **Metadata**: Extract complete tweet metadata including metrics, entities, and user info

## Quick Start

1. Install the package:
```bash
make install
```

2. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your Twitter API credentials
```

3. Run the example:
```bash
cd example
python url_search_run.py --mode search "your_query" --num_posts 20

# Fetch specific tweet by URL
python url_search_run.py --mode url "your_url"
```
