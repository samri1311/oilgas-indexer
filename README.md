# Oil & Gas Intelligent Web Indexer

An intelligent domain-specific web crawler designed to automatically discover, crawl, filter, and index oil & gas industry related web content.

The system uses focused crawling techniques and domain-aware relevance evaluation to extract high-quality information from corporate websites, regulatory portals, industry news platforms, and research institutions.

This project demonstrates how automated web intelligence systems can be built for specialized industries using Python-based crawling frameworks.

---

## Project Overview

The oil & gas industry generates large volumes of unstructured information across websites, regulatory portals, research platforms, and industry publications.

Manually collecting this information is inefficient and difficult to scale.

This project implements an **Intelligent Oil & Gas Web Crawler System** that:

- Automatically discovers relevant industry websites
- Extracts and cleans textual data
- Filters pages using domain-specific relevance detection
- Stores structured text datasets for analytics and research

The crawler is designed to operate continuously while adapting its crawling behavior based on domain performance and content relevance.

---

## Key Features

• Focused crawling for oil & gas domain  
• Automated web scraping using Scrapy  
• Dynamic website rendering using Selenium  
• Domain-specific keyword relevance detection  
• Data cleaning and text extraction  
• Adaptive crawl prioritization  
• Domain reputation tracking and stall detection  
• Structured data corpus generation  

---

## Technology Stack

Programming Language

- Python

Web Crawling Framework

- Scrapy

Dynamic Page Rendering

- Selenium WebDriver

HTML Parsing

- BeautifulSoup

Text Processing

- Custom NLP utilities

Data Storage

- File-based structured corpus

---

## System Architecture

The system follows a modular architecture consisting of multiple components:

1. **Seed and Domain Management Layer**
   - Initializes crawling using predefined oil & gas websites
   - Maintains discovered domains and URL lists

2. **Crawling Engine**
   - Implemented using Scrapy
   - Handles large-scale asynchronous crawling

3. **Dynamic Page Handler**
   - Uses Selenium to render JavaScript-heavy websites

4. **Relevance Evaluation Module**
   - Uses keyword detection and contextual scoring
   - Filters non-relevant pages

5. **Adaptive Intelligence Module**
   - Tracks crawl performance
   - Adjusts crawling priorities dynamically

6. **Data Storage Layer**
   - Stores cleaned textual content by domain
   - Maintains metadata for each page

---

## Workflow

1. Seed URLs are loaded from trusted oil & gas websites
2. The crawler fetches web pages using Scrapy
3. Selenium renders dynamic content when required
4. Extracted pages are evaluated using domain-specific keywords
5. Relevant pages are cleaned and processed
6. New URLs are prioritized for future crawling
7. Cleaned data is stored in a structured corpus

---

## Sample Keywords Used for Relevance Detection

Examples of oil & gas related keywords used by the crawler:

- crude oil
- natural gas
- refinery
- drilling rig
- hydrocarbon
- pipeline infrastructure
- upstream operations
- downstream processing
- petrochemical
- LNG
- energy transition

These keywords help filter relevant industry content during crawling.

---

## Project Structure

oilgas_indexer
│
├── spiders/
│ └── oilgas_spider.py
│
├── utils/
│ ├── relevance_evaluation.py
│ ├── priority_scheduler.py
│ └── domain_reputation.py
│
├── data/
│ └── corpus/
│
├── config/
│ └── keywords.py
│
├── requirements.txt
└── README.md


---

## Installation

Clone the repository:

git clone https://github.com/samri1311/oilgas-indexer.git

cd oilgas-indexer

Install dependencies:

pip install -r requirements.txt


---

## Running the Crawler

Run the crawler using Scrapy:

scrapy crawl oilgas_spider


The crawler will begin collecting and processing oil & gas industry data.

---

## Output

The crawler generates a structured dataset containing:

- cleaned textual content
- source URL
- crawl timestamp
- domain information

Output is stored in domain-wise files for easy analysis.

---

## Applications

This system can support several real-world use cases:

- Oil & Gas market intelligence
- Regulatory monitoring
- Technology trend analysis
- ESG and sustainability tracking
- Data collection for AI and NLP research

---

## Future Improvements

Possible future enhancements include:

- Machine learning based relevance classification
- Distributed crawling infrastructure
- Scalable database storage
- Knowledge graph generation
- Interactive analytics dashboard

---

## Author

Samriddhi Shanker  
Python Developer | Data Engineering | AI Tools

LinkedIn:
https://www.linkedin.com/in/samriddhi-shanker-07o24
