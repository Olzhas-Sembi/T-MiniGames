from fastapi import APIRouter
import feedparser

router = APIRouter()

RSS_URLS = [
    "https://tengrinews.kz/rss/all.xml",
    "https://www.zakon.kz/rss/"
]

@router.get("/news")
def get_news():
    news = []
    for url in RSS_URLS:
        feed = feedparser.parse(url)
        for entry in feed.entries[:5]:
            news.append({
                "title": entry.title,
                "link": entry.link,
                "published": entry.published if 'published' in entry else ''
            })
    return news
