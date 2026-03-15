# Scrapy settings for oilgas_indexer project
#
# For simplicity, this file contains only settings considered important or
# commonly used. You can find more settings consulting the documentation:
#
#     https://docs.scrapy.org/en/latest/topics/settings.html
#     https://docs.scrapy.org/en/latest/topics/downloader-middleware.html
#     https://docs.scrapy.org/en/latest/topics/spider-middleware.html

import os
from shutil import which

BOT_NAME = "oilgas_indexer"
SPIDER_MODULES = ["oilgas_indexer.spiders"]
NEWSPIDER_MODULE = "oilgas_indexer.spiders"

SELENIUM_DRIVER_NAME = "chrome"
SELENIUM_DRIVER_EXECUTABLE_PATH = which("chromedriver") or "chromedriver-win64/chromedriver.exe"
SELENIUM_DRIVER_ARGUMENTS = ["--headless", 
                             "--no-sandbox", 
                             "--disable-gpu"
                             "--disable-dev-shm-usage",
                             "--disable-extensions",
                             "--disable-blink-features=AutomationControlled",
                             "--window-size=1920,1080"]

ADDONS = {}


# Crawl responsibly by identifying yourself (and your website) on the user-agent
#USER_AGENT = "oilgas_indexer (+http://www.yourdomain.com)"

# Obey robots.txt rules
ROBOTSTXT_OBEY = False

# Concurrency and throttling settings
CONCURRENT_REQUESTS = 4
CONCURRENT_REQUESTS_PER_DOMAIN = 2
DOWNLOAD_DELAY = 1

# Disable cookies (enabled by default)
COOKIES_ENABLED = False
LOG_LEVEL = "INFO"


# Disable Telnet Console (enabled by default)
#TELNETCONSOLE_ENABLED = False

# Override the default request headers:
#DEFAULT_REQUEST_HEADERS = {
#    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
#    "Accept-Language": "en",
#}

# Enable or disable spider middlewares
# See https://docs.scrapy.org/en/latest/topics/spider-middleware.html
#SPIDER_MIDDLEWARES = {
#    "oilgas_indexer.middlewares.OilgasIndexerSpiderMiddleware": 543,
#}

# Persist spider state so Scrapy scheduler can resume
JOBDIR = os.path.join("crawl_state", "oilgas")

# Selenium integration (scrapy-selenium middleware or our custom middleware)
SELENIUM_DRIVER_NAME = "chrome"
SELENIUM_DRIVER_EXECUTABLE_PATH = which("chromedriver") or "chromedriver"
SELENIUM_DRIVER_ARGUMENTS = ["--headless", "--no-sandbox", "--disable-gpu"]


# Enable our Smart Selenium middlewares

DOWNLOADER_MIDDLEWARES = {
# "scrapy_selenium.SeleniumMiddleware":800,
 "oilgas_indexer.middlewares.SmartSeleniumMiddleware": 800,

}

# Enable or disable extensions
# See https://docs.scrapy.org/en/latest/topics/extensions.html
#EXTENSIONS = {
#    "scrapy.extensions.telnet.TelnetConsole": None,
#}

# Configure item pipelines

ITEM_PIPELINES = {
    "oilgas_indexer.pipelines.PersistentQueuePipeline": 300,
     #"oilgas_indexer.pipelines.JsonlWriterPipeline": 400,

}
# Enable and configure the AutoThrottle extension (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/autothrottle.html
AUTOTHROTTLE_ENABLED = True
# The initial download delay
AUTOTHROTTLE_START_DELAY = 1
# The maximum download delay to be set in case of high latencies
AUTOTHROTTLE_MAX_DELAY = 10
# The average number of requests Scrapy should be sending in parallel to
# each remote server
AUTOTHROTTLE_TARGET_CONCURRENCY = 2.0
# Enable showing throttling stats for every response received:
#AUTOTHROTTLE_DEBUG = False

# Enable and configure HTTP caching (disabled by default)
# See https://docs.scrapy.org/en/latest/topics/downloader-middleware.html#httpcache-middleware-settings
#HTTPCACHE_ENABLED = True
#HTTPCACHE_EXPIRATION_SECS = 0
#HTTPCACHE_DIR = "httpcache"
#HTTPCACHE_IGNORE_HTTP_CODES = []
#HTTPCACHE_STORAGE = "scrapy.extensions.httpcache.FilesystemCacheStorage"

# Set settings whose default value is deprecated to a future-proof value


# FEED_EXPORT_ENCODING = "utf-8"- not reqd bcoz we use pipelines to save
DUPEFILTER_DEBUG = True
OFFSITE_ENABLED = False
RETRY_ENABLED = True
RETRY_TIMES = 2
DOWNLOAD_TIMEOUT = 25