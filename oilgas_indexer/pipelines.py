# Define your item pipelines here
# useful for handling different item types with a single interface

import re
from bs4 import BeautifulSoup
import json
import os
from datetime import datetime

from urllib.parse import urlparse
import heapq



DATA_DIR = "data"
CORPUS_DIR = os.path.join(DATA_DIR, "corpus")

URL_GRAPH = os.path.join(DATA_DIR, "url_graph.json")
PENDING_FILE = os.path.join(DATA_DIR, "pending_urls.json")
BACKLINK_FILE = os.path.join(DATA_DIR, "backlink_index.json")

WHITESPACE_RE =re.compile(r"\s+")

def ensure_dir():
    os.makedirs(DATA_DIR, exist_ok=True)
    os.makedirs(CORPUS_DIR, exist_ok=True)


    

# --------------------------
# CLEAN TEXT FUNCTION
# --------------------------
'''def clean_text(raw: str) -> str:
    """Clean extracted text for readability."""
    if not raw:
        return ""

    # Remove HTML
    soup = BeautifulSoup(raw, "html.parser")
    for tag in soup(["script", "style", "noscript", "header", "footer", "nav", "svg"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)

    # Regex cleanup
    text = WHITESPACE_RE.sub(" ", text)
    text = re.sub(r"*([,.;:!?])*", r"\1 ", text)
    text = re.sub(r"*\n*", "\n", text)

    return text.strip()   '''     

class PersistentQueuePipeline:
    def open_spider(self, spider):
        #self.data_dir = os.path.join("data", "corpus")
        ensure_dir()
        spider.logger.info(f"🗂 Output folder ready: {CORPUS_DIR}")

    
        # load url_graph (visited)
        spider.url_graph = {}
        spider.visited = set()
        spider.pending = []
        self.backlink_index = {}  # heap of (priority, url)

        for path, target in [
            (URL_GRAPH, "url_graph"),
            (PENDING_FILE, "pending"),
            (BACKLINK_FILE, "backlink_index"),
        ]:

            if os.path.exists(path):
                try:
                    with open(path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                        if target == "url_graph":
                            spider.url_graph = data
                            spider.visited = set(data.keys())
                        elif target == "pending":
                            for entry in data:
                                heapq.heappush(spider.pending, tuple(entry)) 
                        elif target == "backlink_index":
                            self.backlink_index = data 
                except Exception as e:
                    spider.logger.warning(f" ⚠️ Could not load {path}: {e}")
        spider.domain_counts = {}             


    def process_item(self, item, spider):
        # item expected to include: url, title, page_content, links (list)
        url = item.get("url")
        text = item.get("page_content","")
        title = item.get("title", "")
        #links = item.get("links", [])
        
        if not text or len(text.strip()) < 300:
            spider.logger.warning(f"🚫 Skipping save for {url} — text too short or empty")
            return item

        text = re.sub(r"\s+", " ", text).strip() 

        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.","")
        os.makedirs("data/corpus", exist_ok=True)
        filename = f"data/corpus/{domain}.txt"

        #----compute page size----
        size_kb = round(len(text.encode("utf-8"))/1024, 2)
        timestamp = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S")

        with open(filename, "a", encoding="utf-8") as f:
            f.write(f"=== {timestamp} | {url} | {size_kb:.2f} KB ===\n\n")
            f.write(text+"\n\n\n")

        spider.logger.info(f"🧹 Cleaned & saved {url} ({size_kb:.2f} KB) → {filename}")

        spider.domain_counts[domain] = spider.domain_counts.get(domain, 0) + 1

        domain_pages = [u for u in spider.visited if domain in u]
        if len(domain_pages) > 350:  #  cap for irrelevant / huge domains
            spider.logger.info(f"🛑 Capped at {len(domain_pages)} pages for {domain}")

            spider.pending = [
                entry for entry in spider.pending
                if domain not in entry[1]
            ]
            spider.visited.add(f"{domain}#CAPPED")

            with open(PENDING_FILE, "w", encoding="utf-8"):
                json.dump(spider.pending, f, indent=2)
        return item    

        