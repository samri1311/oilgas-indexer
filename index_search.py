import json
from urllib.parse import urlparse
import os
from bs4 import BeautifulSoup
import subprocess
import threading

KNOWN_DOMAINS_FILE = "known_domains.txt"
NEW_EXTERNAL_SEEDS = "new_external_seeds.txt"
CRAWLED_PAGES_DIR = "crawled_pages/"  # folder where your spider saves .html files or JSON

OILGAS_KEYWORDS = [
    "oil", "gas", "petroleum", "refinery", "pipeline", "energy",
    "rig", "hydrogen", "fuel", "offshore", "onshore", "LNG"
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

def extract_external_links():
    known_domains = load_known_domains()
    new_links = set()
    new_domains = set()

    for file in os.listdir(CRAWLED_PAGES_DIR):
        if file.endswith(".html"):
            with open(os.path.join(CRAWLED_PAGES_DIR, file), "r", encoding="utf-8") as f:
                soup = BeautifulSoup(f.read(), "html.parser")
                for tag in soup.find_all("a", href=True):
                    url = tag["href"]
                    domain = urlparse(url).netloc
                    if not domain:
                        continue
                    if domain not in known_domains and any(k in url.lower() for k in OILGAS_KEYWORDS):
                        new_links.add(url)
                        new_domains.add(domain)

    # Save discovered domains
    for domain in new_domains:
        save_known_domain(domain)

    # Save new external URLs
    with open(NEW_EXTERNAL_SEEDS, "w", encoding="utf-8") as f:
        f.write("\n".join(sorted(new_links)))

    print(f"✅ Found {len(new_domains)} new domains and {len(new_links)} new URLs.")

if __name__ == "__main__":
    extract_external_links()
