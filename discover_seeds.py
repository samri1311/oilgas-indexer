# discover_seeds.py
from SPARQLWrapper import SPARQLWrapper, JSON
import re
import time

WIKIDATA_ENDPOINT = "https://query.wikidata.org/sparql"
DBPEDIA_ENDPOINT = "https://dbpedia.org/sparql"

# --- Wikidata Query ---
WIKIDATA_QUERY = """
SELECT DISTINCT ?company ?companyLabel ?website WHERE {
  ?company wdt:P452 wd:Q23442;    # oil and gas industry
           wdt:P856 ?website.     # official website
  SERVICE wikibase:label { bd:serviceParam wikibase:language "en". }
}
"""

# --- DBpedia Query ---
DBPEDIA_QUERY = """
SELECT DISTINCT ?company ?website WHERE {
  ?company dbo:industry dbr:Petroleum_industry;
           foaf:homepage ?website.
}
"""

def fetch_sparql_results(endpoint, query):
    sparql = SPARQLWrapper(endpoint)
    sparql.setQuery(query)
    sparql.setReturnFormat(JSON)
    sparql.setTimeout(60)
    try:
        results = sparql.query().convert()
        return results["results"]["bindings"]
    except Exception as e:
        print(f"[!] Error querying {endpoint}: {e}")
        return []

def extract_websites(results):
    urls = set()
    for r in results:
        if "website" in r:
            url = r["website"]["value"].strip()
            if re.match(r"https?://", url):
                urls.add(url)
    return urls

def main():
    print("🔍 Discovering oil & gas websites from Wikidata...")
    wikidata_results = fetch_sparql_results(WIKIDATA_ENDPOINT, WIKIDATA_QUERY)
    wikidata_urls = extract_websites(wikidata_results)
    print(f"✅ Found {len(wikidata_urls)} from Wikidata")

    time.sleep(2)  # polite delay

    print("🌐 Discovering oil & gas websites from DBpedia...")
    dbpedia_results = fetch_sparql_results(DBPEDIA_ENDPOINT, DBPEDIA_QUERY)
    dbpedia_urls = extract_websites(dbpedia_results)
    print(f"✅ Found {len(dbpedia_urls)} from DBpedia")

    # --- Merge and clean ---
    all_urls = sorted(set(wikidata_urls | dbpedia_urls))
    print(f"🧩 Total unique sites discovered: {len(all_urls)}")

    # --- Write to file ---
    with open("external_seeds.txt", "w", encoding="utf-8") as f:
        for url in all_urls:
            f.write(url + "\n")

    print("💾 Saved to external_seeds.txt")

if __name__ == "__main__":
    main()
