import requests
from datetime import datetime, timedelta
from processing.normalize import normalize_article

def fetch_newsapi(keyword, api_key):
    url = "https://newsapi.org/v2/everything"
    since = (datetime.now() - timedelta(days=2)).strftime("%Y-%m-%d")
    params = {
        "q": keyword,
        "apiKey": api_key,
        "language": "en",
        "sortBy": "publishedAt",
        "from": since,
        "pageSize": 25
    }
    try:
        data = requests.get(url, params=params).json()
        if data.get("status") != "ok":
            print("NewsAPI error:", data.get("message"))
            return []
        return [
            normalize_article(
                item.get("title"),
                item.get("url"),
                item.get("source", {}).get("name"),
                item.get("publishedAt"),
                item.get("urlToImage")
            )
            for item in data.get("articles", [])
        ]
    except Exception as e:
        print("NewsAPI Exception:", e)
        return []
