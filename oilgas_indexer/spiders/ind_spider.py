import scrapy
import requests
from scrapy_selenium import SeleniumRequest
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
import re
import os
import json
import heapq
import time
from datetime import datetime
import subprocess
import threading
import io
from rapidfuzz import fuzz, process
import random
from oilgas_indexer.utils.text_cleaner import clean_text
from oilgas_indexer.utils.crawler_brain import CrawlerBrain

OILGAS_KEYWORDS = [
    "oil", "gas", "petroleum", "refinery", "pipeline",
    "drilling", "upstream", "midstream", "downstream",
    "energy", "rig", "fuel", "petrochemical", "hydrogen",
    "exploration", "crude oil", "well", "central processing facility",
    "reservoir", "porosity", "fracking", "gasification", "barrels per day",
    "LPG", "oil retail sector", "offshore", "onshore", "refinery",
    "distillation unit", "cracking", "hydrocracking",
    "catalytic reforming", "desulfurization", "petrochemicals",
    "lubricants", "gasoline", "diesel", "jet fuel", "bitumen",
    "fuel retail", "distribution network", "marketing outlet",
    "refinery throughput", "Shell", "BP", "ExxonMobil",
    "Chevron", "TotalEnergies", "ONGC", "OIL India",
    "Reliance Industries", "Halliburton", "Schlumberger", "Baker Hughes", "gem", "genscape"
]

DENYLIST_DOMAINS = {
    "youtube.com", "x.com", "twitter.com", "facebook.com", "linkedin.com",
    "instagram.com", "tiktok.com", "reddit.com", "wikipedia.org",
    "osti.gov", "politico.com", "politicopro.com", "copyright.gov", "eenews.net"
}

def extract_domain(url):
    # extract domain safely.
    domain = urlparse(url).netloc.lower()
    domain = domain.replace("www.", "")
    return domain

def bing_background_discovery(keywords, known_domains_file="known_domains.txt", interval=600):
    """
    Background thread that periodically discovers new oil & gas websites from Bing.
    interval: seconds between discovery rounds (default = 10 min)
    """

    headers= {
        "User-Agent": random.choice([
            "Mozilla/5.0 (Windows NT 10.0; Win64; x64)",
            "Mozilla/5.0 (X11; Ubuntu; Linux x86_64; rv:109.0)",
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)",
        ])    

    }  
    print("🛰️  Bing discovery thread started in background...")

    while True:
        try:
            # -- Load known domains to avoid duplicates --
            known = set()
            if os.path.exists(known_domains_file):
                with open(known_domains_file, "r", encoding="utf-8") as f:
                    known = {line.strip().lower() for line in f if line.strip()}

            new_domains = set()
            session = requests.Session()

            for kw in keywords:
                for page in range(0, 2):  # first 2 pages
                    offset = page*10
                    q = f"https://www.bing.com/search?q={kw}+oil+gas+energy&first={offset}"
                    r = session.get(q, headers=headers, timeout=10)  
                    soup = BeautifulSoup(r.text, "html.parser")

                    for a in soup.select("li.b_algo h2 a"):
                        href = a.get("href")
                        if not href or "bing.com" in href:
                            continue

                        domain = extract_domain(href)
                        if (
                            domain
                            and domain not in known
                            and re.search(r"\.(com|org|net|in|ae|sa|uk|co|io|info|energy|biz|gov|int|me|us|ca|au|de|fr|ng|ru)$",domain)
                            and not any(bad in domain for bad in ["facebook", "linkedin", "twitter", "youtube", "wikipedia"])
                            ):
                            new_domains.add(domain)
                    time.sleep(random.uniform(1,3))
            
            if new_domains:
                with open(known_domains_file, "a",encoding="utf-8") as f:
                    for d in sorted(new_domains):
                        f.write(d +"\n")
                print(f"✅ Background added {len(new_domains)} new domains from Bing.")
            else:
                print("ℹ️  No new Bing domains this cycle.") 

        except Exception as e:
            print(f"[Bing background error] {e}")  
        # sleep before next cycle
        time.sleep(interval)                                              


def run_discovery_scripts():
    """Run seed and feed discovery scripts in the background."""
    try:
        subprocess.run(["python", "discover_seeds.py"], check=False)
        subprocess.run(["python", "feed_collector.py"], check=False)
        subprocess.run(["python", "index_search.py"], check=False)
    except Exception as e:
        print(f"⚠️ Discovery scripts failed: {e}")

class OilGasSpider(scrapy.Spider):
    name = "oilgas_indexer"
    allowed_domains = []  # allow all domains
    start_urls = [
        "https://www.ogj.com/",
        "https://www.rigzone.com/",
        "https://www.offshore-technology.com",
        "https://www.worldoil.com",
        "https://www.energyvoice.com",
        "https://www.upstreamonline.com",
        "https://www.hartenergy.com",
        "https://www.oilandgastechnology.net",

        "https://www.shell.com",
        "https://corporate.exxonmobil.com",
        "https://www.bp.com",
        "https://www.chevron.com",
        "https://www.totalenergies.com",
        "https://www.equinor.com",
        "https://www.aramco.com",
        "https://www.slb.com",
        "https://www.bakerhughes.com",
        "https://gem.wiki/",
        "https://www.saudiaramco.com/",

        "https://www.iocl.com",
        "https://www.ongcindia.com",
        "https://www.oil-india.com",
        "https://www.relianceindustries.com",
        "https://www.gailonline.com",
        "https://www.hpcl.in",
        "https://www.bpcl.in",

        "https://www.iea.org",
        "https://www.opec.org",
        "https://www.dghindia.gov.in",
        "https://data.gov.in",
        "https://www.eia.gov/",

        "https://www.subsea7.com",
        "https://www.saipem.com",
        "https://www.technipenergies.com",
        "https://www.dnv.com",
        "https://www.api.org",
        "https://www.spe.org",
        "https://www.ipieca.org",
        "https://www.offshore-europe.co.uk",
        "https://www.energyconnects.com",


        "https://en.wikipedia.org/wiki/Petroleum_industry",
        "https://www.opec.org/",
        "https://www.bp.com/",
        "https://gem.wiki/",
        "https://www.saudiaramco.com/",
        "https://www.exxonmobil.com/",
        
        "https://www.ft.com/oil-gas",
        "https://rss.feedspot.com/oil_and_gas_rss_feeds/",
        "https://worldoil.com/",
        "https://globalenergymonitor.org/projects/global-oil-gas-extraction-tracker/",
        

    ]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.headers = {
            "User-Agent":"Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                         "AppleWebKit/537.36 (KHTML, like Gecko)"
                         "Chrome/120.0.0.0 Safari/537.36"
        }
        self.pending = []
        self.visited = set()
        self.url_graph = {}
        self.domain_data_size = {}
        self.discovered_domains = set()
        self.relevant_domains = set()

        self.discovered_buffer = set()
        self.last_merge_time = time.time()

        self.domain_page_count= {}
        self.domain_start_time={}

        self.domain_failures={}
        self.blacklist = set()
        self.skip_domains = set()
        self.stalled_domains = set()
        self.last_new_domain_time = time.time()

        self.brain = CrawlerBrain()
        self.logger.info("🧠 CrawlerBrain initialized with dynamic tuning.")

        # -- File paths ---
        self.known_domains_file = "known_domains.txt"
        self.external_seeds_file = "external_seeds.txt"

        # --- Load existing known data (if available) ---
        self.known_domains = set()
        if os.path.exists(self.known_domains_file):
            with open(self.known_domains_file,"r", encoding="utf-8") as f:
                self.known_domains = {line.strip() for line in f if line.strip()}

        self.logger.info(f"Loaded {len(self.known_domains)} known domains from file.")
        # ---Bing-based discovery (optional at startup) ---
        #try:
         #   from threading import Thread
           

           # Start Bing discovery as background thread
          #  discovery_thread = Thread(
            #    target=bing_background_discovery, 
             #   args=(OILGAS_KEYWORDS, self.known_domains_file, 3600),
              #  daemon=True

           # )
            #discovery_thread.start()
            #self.logger.info("🛰️ Background Bing discovery thread launched.")
        #except Exception as e:
         #   self.logger.warning(f"⚠️ Could not start Bing discovery thread: {e}") 

    
    def open_spider(self, spider=None): 
        """
        Called once when the spider starts.
        Loads the persistent blacklist of bad domains.
        """ 
        self.blacklist = set()
        if os.path.exists("blacklist.json"):
            try: 
                with open("blacklist.json", "r", encoding="utf-8") as f:
                    self.blacklist = set(json.load(f))
                self.logger.info(f"🕳️ Loaded {len(self.blacklist)} blacklisted domains from disk.")
                
            except Exception as e:
                self.logger.warning(f"⚠️ Could not load blacklist: {e}")

        self.domain_failures = {}
        self.logger.info("✅ Blacklist system initialized.")                     

    def detect_stall(self, current_domain):
        now = time.time()
        # If domain already blacklisted, skip
        if current_domain in self.blacklist or current_domain in self.skip_domains:
            return True

        page_count = self.domain_page_count.get(current_domain, 0)
        start_time = self.domain_start_time.get(current_domain, 0)
        
        if not start_time:
            self.domain_start_time[current_domain] = now
            return False

        elapsed = now - start_time    

        if page_count >400 or elapsed > 1800: #  >400 pages OR >30 min
            self.skip_domains.add(current_domain)
            self.blacklist.add(current_domain)
            self.logger.warning(f"⚠️ Domain stall detected: {current_domain} "
                                f"(page_count={page_count}, time={elapsed/60:.1f}m) → Skipping further URLs.")
        

            if hasattr(self, "pending"):
                before = len(self.pending)
                self.pending = [(p,u) for p,u in self.pending
                            if urlparse(u).netloc.replace("www.", "")!= current_domain]

                after = len(self.pending)
                self.logger.info(f"🧹 Pruned pending queue for stalled domain {current_domain}")                
                try:
                    with open("blacklist.json", "w", encoding="utf-8") as f:
                        json.dump(list(self.blacklist), f, indent = 2)
                except Exception as e:
                    self.logger.warning(f"⚠️ Could not save updated blacklist: {e}")
                return True
            return False    


    def load_new_external_seeds(self):
        new_seeds = []
        if os.path.exists("known_domains.txt"):
            with open("known_domains.txt", "r", encoding="utf-8") as f:
                domains = [line.strip() for line in f if line.strip()]

            for d in domains:
                if not d.startswith("http"):
                    d = f"https://{d}"
                new_seeds.append(d)

        if not new_seeds and hasattr(self, "start_urls"):
            new_seeds = list(self.start_urls)

        self.logger.info(f"[AUTO-EXPAND] Loaded {len(new_seeds)} new seed URLs from known domains.")
        return new_seeds

    def compute_priority(self, url, snippet, text=""):
        # Compute adaptive crawl priority based on relevance and domain health.
        
        domain = urlparse(url).netloc
        url_lower = url.lower()
        snippet_lower = snippet.lower()
        text_lower = text.lower() if text else ""

        #-- Base score from relevance --
        score = sum(k in snippet.lower() for k in OILGAS_KEYWORDS)

        # Penalize stalled or oversampled domains
        if domain in getattr(self, "stalled_domains", set()):
            return 0

        page_count = self.domain_page_count.get(domain, 0)
        if page_count> 50:
            score-=2

        # - Keyword boost from URL/domain ---
        for kw in OILGAS_KEYWORDS:
            if kw in domain or kw in url_lower:
                score += 5
                break
        
        for kw in OILGAS_KEYWORDS:
            if kw in text.lower():
                score += 2
                break

        # --- Link graph bonus: importance of this node --
        outlinks = len(self.url_graph.get(url, []))
        if outlinks > 5:       
            score += min(outlinks / 10,3)
            score+=1
        return max(score, 0)

    def merge_discoveries(self):
        """Merge newly discovered domains and URLs from previous runs."""
        discovered_domains_file = "discovered_domains.txt"
        new_external_seeds_file = "new_external_seeds.txt"
        known_domains_file = "known_domains.txt"
        external_seeds_file = "external_seeds.txt"

        updated_domains = set()
        updated_seeds = set()

        # --- Load existing known domains ---
        if os.path.exists(discovered_domains_file):
            with open(discovered_domains_file, "r", encoding="utf-8") as f:
                new_domains = [line.strip() for line in f if line.strip()]
                updated_domains.update(new_domains)
            os.remove(discovered_domains_file)
            self.logger.info(f"Merged {len(new_domains)} new discovered domains.")

        if os.path.exists(known_domains_file):
            with open(known_domains_file, "r", encoding="utf-8") as f:
                updated_domains.update([line.strip() for line in f if line.strip()])

        if os.path.exists(external_seeds_file):
            with open(external_seeds_file, "r", encoding="utf-8") as f:
                updated_seeds.update(line.strip() for line in f if line.strip()) 

        if os.path.exists(new_external_seeds_file):
            with open(new_external_seeds_file, "r", encoding="utf-8") as f:
                new_seeds = [line.strip() for line in f if line.strip()]
                updated_seeds.update(new_seeds)
            os.remove(new_external_seeds_file)
            self.logger.info(f"Merged {len(new_seeds)} new external seed URLs.") 

        # --- Write back---                      

        with open(known_domains_file, "w", encoding="utf-8") as f:
            for d in sorted(updated_domains):
                f.write(d + "\n")


        with open(external_seeds_file, "w", encoding="utf-8") as f:
            for s in sorted(updated_seeds):
                f.write(s + "\n")

        self.logger.info(f"✅ Merge complete: {len(updated_domains)} domains and {len(updated_seeds)} seed URLs.")

    def start_requests(self):
        """
    Step 0: Resume from backup if exists.    
    Step 1: Load start URLs from known_domains.txt + start_urls
    Step 2: Merge them into a unified list
    Step 3: Begin crawling — auto-expands without external scripts
    """ 
        print("🚀 start_requests() triggered — preparing URLs...")

        for file in ["known_domains.txt", "external_seeds.txt"]:
            if os.path.exists(file):
                with open(file, "r", encoding="utf-8") as f:
                    lines = sorted(set(line.strip() for line in f if line.strip()))
                with open(file, "w", encoding="utf-8") as f:
                    for line in lines:
                        f.write(line +"\n")

        self.pending = []
        if os.path.exists("pending_backup.txt"):
            with open("pending_backup.txt","r", encoding="utf-8") as f:
                pending_lines = [line.strip() for line in f if line.strip()]
            if len(set(pending_lines)) >=5:
                self.pending = [(0, url) for url in sorted(set(pending_lines))]    
                self.logger.info(f"Resumed {len(self.pending)} pending URLs from backup.")
            else:
                self.logger.warning("⚠️ Pending queue too small or repetitive — resetting crawl state.")   

        self.merge_discoveries()
        seed_urls, domain_urls = [], []

        # --- Load known domains ---
        if os.path.exists("known_domains.txt"):
            with open("known_domains.txt", "r", encoding="utf-8") as f:
                domain_list = [line.strip() for line in f if line.strip()]
                domain_urls = [f"https://{d}" if not d.startswith("http") else d for d in domain_list]
            self.logger.info(f"Loaded {len(domain_urls)} domains from known_domains.txt")
        else:
            self.logger.warning("known_domains.txt not found — creating new one.")
            open("known_domains.txt", "w", encoding="utf-8").close()
        

        # --- Load external seeds ---
        if os.path.exists("external_seeds.txt"):
            with open("external_seeds.txt", "r", encoding="utf-8") as f:
                seed_urls = [line.strip() for line in f if line.strip()]
            self.logger.info(f"Loaded {len(seed_urls)} URLs from external_seeds.txt")

            open("external_seeds.txt", "w").close()  # clear after load
        else:
            self.logger.warning("external_seeds.txt not found — using default seeds.")

        

        # --- Merge all sources ---
        all_start_urls = list(set(self.start_urls + seed_urls + domain_urls))
        self.logger.info(f"Starting crawl with {len(all_start_urls)} total start URLs.")

        # Add the print line here for quick feedback
        print(f"🚀 Launching crawl with {len(all_start_urls)} start URLs.")

        # --- Auto-expand if empty ---
        if not all_start_urls:
            self.logger.warning("# --- Auto-expand if empty ---")
            fallback_seeds = ["https://www.shell.com",
                              "https://www.bp.com",
                              "https://www.saudiaramco.com",
                              "https://www.exxonmobil.com",
                              "https://www.chevron.com",
                              "https://www.totalenergies.com",
                              "https://www.opec.org",
                              "https://www.relianceindustries.com"]
            all_start_urls.extend(fallback_seeds)
            self.logger.info(f"[FALLBACK] added {len(fallback_seeds)} fallback oil and gas sites.") 

        self.logger.info(f"🌍 Starting crawl with {len(all_start_urls)} total start URLs.")    
        print(f"🚀 Launching crawl with {len(all_start_urls)} start URLs.")

        if self.pending:
            self.logger.info(f"Resuming from {len(self.pending)} pending URLs.")
            while self.pending:
                _, url = heapq.heappop(self.pending)
                yield SeleniumRequest(
                    url = url,
                    callback = self.parse,
                    errback = self.handle_error,
                    wait_time = 15,
                    dont_filter = True,
                    )
        else:
            self.logger.info("No valid pending queue found — starting fresh crawl.")
            for url in all_start_urls:
                domain = urlparse(url).netloc.replace("www.", "")
                self.domain_start_time.setdefault(domain, time.time())
                
                yield SeleniumRequest(
                    url = url,
                    callback = self.parse,
                    errback = self.handle_error,
                    wait_time = 15,
                    dont_filter = True,
                    )  
        self.logger.info("✅ All SeleniumRequests yielded to Scrapy — waiting for scheduler...")                  
        
               
    def is_relevant(self, url, snippet=""):
        """
        Determines if a URL/snippet is contextually related to oil & gas.
        Uses layered logic: keyword match + fuzzy score + co-occurrence + density + URL hints.
        """
        text = f"{url} {snippet}".lower()

        # --- Quick denylist filter ---
        if any(d in text for d in DENYLIST_DOMAINS):
            return False

        # --- Tokenize to avoid partial word matches ---
        tokens = re.findall(r"\b[a-zA-Z][a-zA-Z0-9\-]{1,}\b", text)
        token_text = " ".join(tokens)
        total_tokens = len(tokens) or 1

        
        match_count=0
        score=0
        matched_keywords = set()

        # --- 1️⃣ Exact keyword and multi-word match ---
        
        for kw in OILGAS_KEYWORDS:
            kw_low = kw.lower()
            # Allow multi-word keyword handling like "crude oil"
            if " " in kw_low:
                if kw_low in text:
                    score += 3
                    matched_keywords.add(kw_low)
            else:
                if kw_low in tokens:
                    score += 2
                    matched_keywords.add(kw_low)

        # Early reject: no hits at all
        if not matched_keywords and len(tokens)>30:
            return False            

        # --- Apply semantic logic ---
        # 2️⃣ Fuzzy similarity (semantic approximation)
        fuzzy_score=0
        for kw in OILGAS_KEYWORDS:
            for token in tokens[:600]:
                fuzzy = fuzz.partial_ratio(kw.lower(), token)

            
                if fuzzy>85:
                    score+=2
                elif fuzzy >70:
                    score+=1   

        #total_score = match_count+ fuzzy_score

         # --- 3️⃣ Context pair boosts ---
        context_pairs = [("drilling", "rig"), ("offshore", "platform"), ("refinery", "output"), 
                          ("exploration", "well"), ("pipeline", "transport"), ("production", "capacity"),
                            ("barrels", "day"),("upstream", "operations"), ("midstream", "logistics"),
                            ("downstream", "retail"),]
        for a, b in context_pairs:
            if a in token_text and b in token_text:
                score+=3

        # --- 4️⃣ URL / domain hints ---
        if re.search(r"/(oil|gas|refinery|pipeline|energy|upstream|downstream)/", url):
            score+=4
        if  any(kw in url for kw in ["oilgas", "rigzone", "ogj", "petroleum"]):
            score+=2

        # --- 5️⃣ Density check (filter generic mentions) ---
    

        # --- 6️⃣ Final confidence threshold ---      


        # --- Fallback: check for related sector words ---
        related_terms = [
            "oil", "gas", "petroleum", "refinery", "pipeline", "drilling",
            "upstream", "midstream", "downstream", "energy", "rig", "fuel",
            "petrochemical", "hydrogen", "exploration", "crude oil", "well",
            "central processing facility", "reservoir", "porosity", "fracking",
            "gasification", "barrels per day", "LPG", "oil retail sector",
            "offshore", "onshore", "distillation unit", "cracking",
            "hydrocracking", "catalytic reforming", "desulfurization",
            "petrochemicals", "lubricants", "gasoline", "diesel", "jet fuel",
            "bitumen", "fuel retail", "distribution network", "marketing outlet",
            "refinery throughput"
        ]
        if any(rt in tokens for rt in related_terms):
            score+=1



        # --- 6️⃣ Final confidence threshold + density ---
        density= score/total_tokens
        if density <0.005 and score<4:
            return False

        try:
            with open("known_domains.txt","r", encoding="utf-8") as f:
                domain_count = len(f.readlines())
        except FileNotFoundError:
            domain_count = 0  
        threshold = 3 if domain_count >30 else 2
        if density <0.002 and score < 3:
            return False
        return score>=threshold          



    
    def parse(self, response):

        url = response.url.split("#")[0].rstrip("/")
        current_domain = urlparse(response.url).netloc.replace("www.","")

        self.domain_start_time.setdefault(current_domain, time.time())

        if self.detect_stall(current_domain):
            self.logger.warning(f"⏩ Skipping stalled domain early: {current_domain}")
            return


        if url in self.visited:
            self.logger.debug(f"[SKIP] Already visited: {url}")
            return 

        if current_domain in self.blacklist:
            self.logger.warning(f"🚫 Skipping blacklisted domain: {current_domain}")
            return  

        if response.status in [408, 500, 503]:
            self.detect_stall(current_domain, reason=f"HTTP {response.status}")
            return

        if response.url.endswith(".xml") or "sitemap" in response.url.lower():
            self.logger.info(f"🗺️ Sitemap detected at {response.url} — delegating to handle_sitemap()")
            yield from self.handle_sitemap(response)
            return    

        links = response.xpath("//a[@href]/@href").getall()
        if len(links) > 1000:
            self.logger.warning(f"⚠️ {current_domain} generated {len(links)} links → blacklisted")
            self.blacklist.add(current_domain)
            return    


        print(f"🕸️  Parsing response from {response.url}")

        if response.url.endswith(".xml") or "sitemap" in response.url:
            self.logger.info(f"🗺️ Detected sitemap XML: {response.url}")
            yield from self.handle_sitemap(response)
            return
        start_time = time.time()
        MAX_DEPTH = 6
        #url = response.url.split("#")[0].rstrip("/")
        current_depth = response.meta.get("depth", 0)

        # --- Adaptive depth from CrawlerBrain ---
        #self.brain.run_metrics["depth_limit"] 


        self.domain_page_count[current_domain]= self.domain_page_count.get(current_domain, 0)+1
        self.domain_start_time.setdefault(current_domain, time.time())

        # calculate  elapsed time and pages seen
        elapsed = time.time() - self.domain_start_time[current_domain]
        page_count = self.domain_page_count[current_domain]

        if not hasattr(self, "same_domain_count"):
            self.same_domain_count = 0
            self.last_domain = None

        # ⚙️ Activity-based stall detection
        if elapsed > 600 and page_count < 20:  # 10 minutes, <20 pages => probably stuck
            self.logger.warning(f"⏩ Stalled on {current_domain} for {elapsed:.1f}s with only {page_count} pages — skipping domain.")
            self.stalled_domains.add(current_domain)
            return

        if page_count >350:
            self.logger.info(f"🛑 Capped at 350 pages for {current_domain}")
            self.stalled_domains.add(current_domain)
            return

        if current_domain in self.stalled_domains:
            self.logger.debug(f"⏩ Domain already exhausted: {current_domain}")
            return

             
        # --- Respect adaptive depth limit ---
        if current_depth > MAX_DEPTH:
            self.logger.info(f"[SKIP] Depth limit reached for {url}")
            return

        self.visited.add(url)
        page_text = clean_text(response.text) # clean snippet preview
        
        if page_text:
            domain = urlparse(url).netloc.replace("www.","")
            save_dir = "data/corpus"
            os.makedirs(save_dir, exist_ok=True)
            path = os.path.join(save_dir, f"{domain}.txt")

            try: 
                with open(path, "a", encoding="utf-8") as f:
                    snippet = page_text.strip()[:12000]
                    f.write(f"\n\n# --- {url} ---\n{snippet}\n")
                self.logger.info(f"🧾 Saved snapshot for {domain} ({len(page_text)/1024:.1f} KB)")
            except Exception as e:
                self.logger.warning(f"⚠️ Could not save page for {url}: {e}")  

        is_rel = False
        snippet = page_text[:600].lower()
        base_domain = urlparse(url).netloc.replace("www.", "")

        if base_domain not in self.relevant_domains:
            if self.is_relevant(url, snippet):
                self.relevant_domains.add(base_domain)
                is_rel = True 
                self.logger.info(f"🌍 Marked domain as oil & gas relevant: {base_domain}")
            else
                self.logger.debug(f"[SKIP] Irrelevant domain: {base_domain}")
        else
            is_rel = True                     

        if not page_text:
            if not hasattr(self, "empty_retry"):
                self.empty_retry = set()
            if url not in self.empty_retry:
                self.empty_retry.add(url)    
                self.logger.warning(f"⚠️ Empty page text for {url} — retrying once")
                yield SeleniumRequest(url=url, callback=self.parse, dont_filter=True)

            else:
                self.logger.debug(f"🧹 Skipping {url} permanently after empty retry.")    
            return
        snippet = page_text[:600].lower()
        base_domain = urlparse(url).netloc.replace("www.", "")

        if base_domain not in self.relevant_domains:
            if self.is_relevant(url, snippet):
                self.relevant_domains.add(base_domain)
                self.logger.info(f"🌍 Marked domain as oil & gas relevant: {base_domain}")
            else:
                self.logger.debug(f"[SKIP] Irrelevant domain: {base_domain}") 
        title = response.xpath("//title/text()").get() or ""      

        # --- Record metrics for brain learning ---
        latency= time.time() - start_time
        self.brain.record_latency(latency)
        self.brain.record_page(True)
        self.brain.update_domain_reputation(current_domain, is_rel)

        # --- Discover new external domains ---
        raw_links = response.xpath("//a[@href]/@href").getall()
        links = [urljoin(response.url, href) for href in raw_links if href.startswith("http")]
        
        for link in links:
            parsed = urlparse(link)
            base_domain = parsed.netloc.replace("www.","")

            if not base_domain or base_domain == current_domain:
                continue
            if any(d in base_domain for d in DENYLIST_DOMAINS):
                continue
            if base_domain not in self.relevant_domains:
                if not self.is_relevant(link, snippet):
                    continue   
            

            # --- Add to discovered domains and buffer before merge ---
            if base_domain not in self.discovered_domains:
                self.discovered_domains.add(base_domain)
                self.discovered_buffer.add((base_domain, link))   

                # Periodically merge discoveries every 3–5 minutes
                now = time.time()
                if now - self.last_merge_time>180:
                    with open("known_domains.txt", "a", encoding="utf-8") as f:
                        for d, _ in self.discovered_buffer:
                            f.write(d + "\n")
                    with open("discovered_domains.txt", "a", encoding="utf-8") as f:
                        for d, _ in self.discovered_buffer:
                            f.write(d + "\n")
                    with open("external_seeds.txt", "a", encoding="utf-8") as f:
                        for _, l in self.discovered_buffer:
                            f.write(l + "\n")        

                    self.logger.info(f"[AUTO-MERGE] Wrote {len(self.discovered_buffer)} new discoveries to disk.")
                    self.discovered_buffer.clear()
                    self.last_merge_time = now                    

            # --- Compute link priority for later crawl ---
            if base_domain in self.relevant_domains:
                priority = 5
            else:    
                priority = self.compute_priority(link, snippet)
            if link not in self.visited:
                if self.domain_page_count.get(base_domain, 0) > 300:
                    continue
                heapq.heappush(self.pending, (-priority, link))

                if self.domain_page_count:
                # Only crawl if high enough priority
                    if priority >= 3:
                        yield SeleniumRequest(url=link, callback=self.parse, dont_filter=True)

        # --- Track data volume ---
        timestamp = datetime.utcnow().isoformat() + "Z"
        page_bytes = len(response.body or b"")
        page_kb = round(page_bytes / 1024, 2)
        domain = urlparse(url).netloc.replace("www.", "")

        self.domain_data_size[current_domain] = self.domain_data_size.get(current_domain, 0) + page_kb
        total_kb = self.domain_data_size[domain]

        try:
            safe_domain = current_domain.replace("/","_")
            os.makedirs(f"data/corpus", exist_ok= True)
            save_path = f"data/corpus/{safe_domain}.txt"
            with open(save_path, "a", encoding = "utf-8") as f:
                f.write(f"\n\n##### {title.strip() or 'No Title'} — {url}\n")
                f.write(page_text[:50000])
            self.logger.info(f"🧾 Saved page → {save_path}")
        except Exception as e:
            self.logger.error(f"❌ Failed to save {url}: {e}")   

        yield {
            "url": url,
            "title": title,
            "page_content": page_text,
            "links": links,
            "timestamp": timestamp,
            "page_size_kb": page_kb,
            "total_site_data_kb": total_kb,
            "domain": current_domain,
        }

        self.brain.tune(self.logger)
        if self.brain.run_metrics["page_count"] %10==0:
            self.brain.save_stats() 
    def handle_sitemap(self, response):
        """Parse sitemap XML and yield SeleniumRequests for each listed <loc> URL."""
        try:
            soup = BeautifulSoup(response.text, "xml")
            loc_tags = soup.find_all("loc")  
            if not loc_tags:
                self.logger.warning(f"⚠️ No <loc> tags found in sitemap: {response.url}") 
                return
            count = 0
            for loc in loc_tags:
                link = loc.text.strip()
                if not link.startswith("http"):
                    continue

                count+=1
                yield SeleniumRequest(
                    url = link,
                    callback = self.parse,
                    dont_filter = True,
                )
            self.logger.info(f"🗺️ Extracted {count} URLs from sitemap: {response.url}")
        except Exception as e:
             self.logger.error(f"❌ Failed to process sitemap {response.url}: {e}")                                 

    def handle_error(self, failure):
        # "Handle failed or timed-out SeleniumRequests gracefully"
        try:
            url = failure.request.url
        except Exception:
            url= "Unknown URL"

        self.logger.warning(f"⚠️ Request failed or timed out: {url}")
        self.logger.debug(repr(failure))  # detailed traceback for debugging

        #   --- Remove from pending queue (to avoid infinite loop) ---
        if hasattr(self, "pending"):
            self.pending = [(p,u) for p,u in self.pending if u!=url]
            
            self.logger.info(f"Removed {url} from pending queue after failure.") 


    def close(self, reason):
        """When spider finishes, save newly discovered domains and pending URLs."""

        if self.discovered_domains:
            output_file = "discovered_domains.txt"
            with open(output_file, "a", encoding="utf-8") as f:
                for d in sorted(self.discovered_domains):
                    f.write("https://" + d + "\n")
            self.logger.info(f"✅ Saved {len(self.discovered_domains)} new candidate domains to {output_file}")
        else:
            self.logger.info("No new domains discovered.")

        # --- Save pending URLs (resume support) ---
        try:
            if getattr(self, "pending", None):
                with open("pending_backup.txt", "w", encoding="utf-8") as f:
                    for _, url in self.pending:
                        f.write(url+"\n")
            else:
                self.logger.info(f"💾 Saved {len(self.pending)} pending URLs before shutdown.") 
        except Exception as e:
            self.logger.warning(f"⚠️ Could not save pending URLs: {e}")  

        try:
            with open("blacklist.json", "w", encoding="utf-8") as f:
                json.dump(list(self.blacklist), f, indent=2)
            self.logger.info(f"💾 Saved {len(self.blacklist)} blacklisted domains to disk.")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not save blacklist: {e}")  

        try:
            if self.relevant_domains:
                with open("relevant_domains.txt", "w", encoding="utf-8") as f:
                    for d in sorted(self.relevant_domains):
                        f.write("https://"+ d + "\n")
                self.logger.info(f"💾 Saved {len(self.relevant_domains)} relevant domains to relevant_domains.txt")
        except Exception as e:
            self.logger.warning(f"⚠️ Could not save relevant domains: {e}")                                           

       