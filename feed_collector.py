import requests
import feedparser
import os
from urllib.parse import urlparse

OILGAS_KEYWORDS = [
    "oil", "gas", "petroleum", "refinery", "pipeline",
    "drilling", "energy", "offshore", "onshore",
    "hydrogen", "fuel", "petrochemical", "crude", "rig", "LPG",
    "uptream","midstream","downstream","exploration","production",
    "LNG","desulphurization","refinery throughput","distribution network",
    "hydrogen","carbon trading","oil futures","Shell",
    "BP",
    "ExxonMobil",
    "Chevron",
    "TotalEnergies",
    "ONGC",
    "OIL India",
    "Reliance Industries",
    "Halliburton",
    "Schlumberger",
    "Baker Hughes",
]

KNOWN_DOMAINS_FILE = "known_domains.txt"
EXTERNAL_SEEDS_FILE = "external_seeds.txt"
FEED_LOG_FILE = "feed_discovery_log.json"

GOOGLE_NEWS_RSS = [
    "https://news.google.com/rss/search?q=oil+gas+energy",
    "https://news.google.com/rss/search?q=petroleum+refinery",
    "https://news.google.com/rss/search?q=offshore+drilling",
    "https://news.google.com/rss/search?q=hydrogen+energy"
    "https://www.ogj.com/rss",
    "https://oilprice.com/rss/main.xml",
    "https://www.rigzone.com/rss/news/",
    "https://energyvoice.com/feed/",
    "https://www.offshore-technology.com/feed/",
    "https://www.hartenergy.com/rss"
]

def load_known_domains():
    if not os.path.exists(KNOWN_DOMAINS_FILE):
        return []
    with open(KNOWN_DOMAINS_FILE, "r", encoding="utf-8") as f:
        return [line.strip() for line in f if line.strip()]

def save_known_domain(domain):
    domains = load_known_domains()
    if domain not in domains:
        with open(KNOWN_DOMAINS_FILE, "a", encoding="utf-8") as f:
            f.write(domain + "\n")

def collect_feeds():
    seed_urls = set()
    domains = load_known_domains()

    print(f"🔍 Checking feeds from {len(domains)} known domains...")

    # Try to access /rss or /feed for each known domain
    for domain in domains:
        for endpoint in ["/rss", "/feed", "/feeds", "/news/feed"]:
            url = f"https://{domain}{endpoint}"
            try:
                response = requests.get(url, timeout=10)
                if response.status_code == 200 and "xml" in response.headers.get("Content-Type", ""):
                    feed = feedparser.parse(response.text)
                    for entry in feed.entries:
                        if any(k in entry.title.lower() for k in OILGAS_KEYWORDS):
                            seed_urls.add(entry.link)
                break
            except Exception:
                continue

    # Include Google News keyword-based RSS
    print("📰 Fetching keyword-based Google News feeds...")
    for url in GOOGLE_NEWS_RSS:
        feed = feedparser.parse(url)
        for entry in feed.entries:
            if any(k in entry.title.lower() for k in OILGAS_KEYWORDS):
                seed_urls.add(entry.link)
                domain = urlparse(entry.link).netloc
                save_known_domain(domain)

    print(f"✅ Collected {len(seed_urls)} unique URLs.")
    with open(EXTERNAL_SEEDS_FILE, "w", encoding="utf-8") as f:
        f.write("\n".join(seed_urls))

if __name__ == "__main__":
    collect_feeds()
