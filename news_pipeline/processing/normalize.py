def normalize_article(title, link, source, summary, date, image=None):
    return {
        "title": title or "No Headline",
        "link": link or "#",
        "source": str(source or "").upper(),
        "summary": (summary or "No summary available.")[:1000],
        "published_at": date or "",
        "image": image or "https://via.placeholder.com/150"
    }
