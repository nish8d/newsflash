from typing import Any, Dict


def normalize_article(*args, **kwargs) -> Dict[str, Any]:
    """
    Supported call styles:

    normalize_article(title, link, source, date)
    normalize_article(title, link, source, date, image)

    This makes the pipeline fully backward-compatible.
    """

    # unpack based on actual arg count
    title      = args[0] if len(args) > 0 else None
    link       = args[1] if len(args) > 1 else None
    source     = args[2] if len(args) > 2 else None
    date       = args[3] if len(args) > 3 else None
    image      = args[4] if len(args) > 4 else None

    # args[5] might be summary → ignore safely

    return {
        "title": title or "No Headline",
        "link": link or "#",
        "source": str(source or "").upper(),
        "published_at": date or "",
        "image": image or "https://via.placeholder.com/150"
    }
