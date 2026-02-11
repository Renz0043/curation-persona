from .newsletter_fetcher import NewsletterFetcher
from .registry import FetcherRegistry
from .rss_fetcher import RSSFetcher
from .website_fetcher import WebsiteFetcher

fetcher_registry = FetcherRegistry()
fetcher_registry.register(RSSFetcher())
fetcher_registry.register(WebsiteFetcher())
fetcher_registry.register(NewsletterFetcher())

__all__ = ["fetcher_registry", "FetcherRegistry", "BaseFetcher"]
