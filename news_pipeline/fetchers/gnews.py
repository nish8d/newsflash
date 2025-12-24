import requests
from processing.normalize import normalize_article

def fetch_gnews(keyword, api_key, country="in"):
    url = "https://gnews.io/api/v4/search"
    params = {
        'token': api_key,
        'q': keyword,
        'lang': 'en',
        'country': country,
        'sortby': 'publishedAt',
        'max': 25
    }
    try:
        data = requests.get(url, params=params).json()
        if "errors" in data:
            print("GNews Error:", data["errors"])
            return []
        return [
            normalize_article(
                item.get("title"),
                item.get("url"),
                item.get("source", {}).get("name"),
                item.get("publishedAt"),
                item.get("image")
            )
            for item in data.get("articles", [])
        ]
    except Exception as e:
        print("GNews Exception:", e)
        return []
