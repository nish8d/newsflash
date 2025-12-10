import requests
from processing.normalize import normalize_article

def fetch_newsdata(keyword, api_key, country="in", category="business"):
    url = "https://newsdata.io/api/1/news"
    params = {
        'apikey': api_key,
        'q': keyword,
        'language': 'en',
        'country': country,
        'category': category
    }
    try:
        data = requests.get(url, params=params).json()
        if data.get("status") != "success":
            print("NewsData error:", data.get("results"))
            return []
        return [
            normalize_article(
                item.get("title"),
                item.get("link"),
                item.get("source_id"),
                item.get("description"),
                item.get("pubDate"),
                item.get("image_url")
            )
            for item in data.get("results", [])
        ]
    except Exception as e:
        print("NewsData Exception:", e)
        return []
