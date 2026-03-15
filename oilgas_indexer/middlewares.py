from scrapy.http import HtmlResponse
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, WebDriverException
import time
import logging
from webdriver_manager.chrome import ChromeDriverManager


class SmartSeleniumMiddleware:
    def __init__(self):
        self.log = logging.getLogger("SmartSeleniumMiddleware")
        self.driver = self._create_driver()
        self.page_counter = 0

    def _create_driver(self):
        chrome_options = Options()
        chrome_options.add_argument("--headless=new")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-extensions")
        chrome_options.add_argument("--disable-blink-features=AutomationControlled")
        chrome_options.add_argument("--window-size=1920,1080")
        chrome_options.add_argument("--log-level=3")

        # ✅ Key fixes for Chrome DNS crash and memory stability
        chrome_options.add_argument("--dns-prefetch-disable")       # Prevents DNS cache overload
        chrome_options.add_argument("--disable-background-timer-throttling")
        chrome_options.add_argument("--disable-background-networking")
        chrome_options.add_argument("--disable-software-rasterizer")
        chrome_options.add_argument("--no-first-run")
        chrome_options.add_argument("--no-default-browser-check")

        if not hasattr(self, "_service"):
            self._service = Service(ChromeDriverManager().install())

        driver = webdriver.Chrome(service=self._service, options=chrome_options)
        driver.set_page_load_timeout(25)
        return driver

    def _restart_driver(self, spider=None):
        """Restart driver to prevent memory leaks."""
        try:
            self.driver.quit()
        except Exception:
            pass
        time.sleep(2)
        self.driver = self._create_driver()
        msg = "🔄 Restarted Selenium driver due to invalid session."
        if spider:
            spider.logger.info(msg)
        else:
            self.log.warning(msg)

    def process_request(self, request, spider):
        """Render JS-heavy pages using Selenium before passing HTML to Scrapy."""
        try:
            if self.driver is None:
                self._restart_driver(spider)
            self.driver.get(request.url)

            # Wait until the <body> tag exists or timeout
            WebDriverWait(self.driver, 15).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )

            last_height = self.driver.execute_script("return document.body.scrollHeight")

            for _ in range(6):
                # Scroll a bit each time to trigger lazy-loading
                self.driver.execute_script("window.scrollBy(0, document.body.scrollHeight / 5);")
                time.sleep(1.5)

                # --- Try clicking "Load more" buttons if visible ---
                try:
                    load_more = self.driver.find_elements(
                        "xpath",
                        "//*[contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'load more') or "
                        "contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'show more') or "
                        "contains(translate(text(),'ABCDEFGHIJKLMNOPQRSTUVWXYZ','abcdefghijklmnopqrstuvwxyz'), 'view more')]"
                    )
                    if load_more:
                        try:
                            self.driver.execute_script("arguments[0].scrollIntoView(true);", load_more[0])
                            self.driver.execute_script("arguments[0].click();", load_more[0])
                            time.slep(2)
                        except Exception as e:
                            # Fallback: JS-based click
                            self.log.debug(f"[LoadMore] Click failed: {e}")
                    
                except Exception as e:
                    self.log.debug(f"[LoadMore] Skipped: {e}")

                # --- Try clicking pop-ups like Accept/OK/Close ---
                try:
                    self.driver.execute_script("""
                        for (let el of document.querySelectorAll('button, a')) {
                            if (/accept|agree|close|ok/i.test(el.innerText)) el.click();
                        }
                    """)
                except Exception:
                    pass

                # Stop scrolling if page stopped expanding
                new_height = self.driver.execute_script("return document.body.scrollHeight")
                if new_height == last_height:
                    break
                last_height = new_height

            # Wait for JS-heavy sections to stabilize
            time.sleep(2)
            html = self.driver.page_source
            self.page_counter += 1

            # Restart Selenium after every 80 pages (memory cleanup)
            if self.page_counter % 80 == 0:
                spider.logger.info("♻️ Restarting Selenium driver after 80 pages")
                self._restart_driver(spider)

            # Return rendered HTML as Scrapy Response
            return HtmlResponse(
                url=self.driver.current_url,
                body=html,
                encoding="utf-8",
                request=request,
            )

        except TimeoutException:
            spider.logger.warning(f"⏱️ Timeout loading {request.url}")
            try:
                self.driver.execute_script("window.stop();")
            except Exception:
                pass
            return HtmlResponse(url=request.url, status=408, request=request)

        except WebDriverException as e:
            spider.logger.info(f"💥 WebDriver crashed on {request.url}: {e}")
            self._restart_driver(spider)
            return HtmlResponse(url=request.url, status=500, request=request)

        except Exception as e:
            spider.logger.error(f"❌ Unexpected Selenium error on {request.url}: {e}")
            return HtmlResponse(url=request.url, status=500, request=request)

    def __del__(self):
        """Ensure driver quits cleanly on shutdown."""
        try:
            self.driver.quit()
        except Exception:
            pass
