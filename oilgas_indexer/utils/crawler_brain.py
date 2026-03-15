# crawler_brain.py
import json, time, os, statistics

class CrawlerBrain:
    def __init__(self, stats_file="domain_stats.json"):
        self.stats_file = stats_file
        self.domain_stats = {}
        self.run_metrics = {
            "pages": 0,
            "relevant": 0,
            "avg_latency": 0.0,
            "depth_limit": 4,
            "download_delay": 1.0
        }
        self._load_stats()

    # -----------------------------
    # Persistent learning memory
    # -----------------------------
    def _load_stats(self):
        if os.path.exists(self.stats_file):
            try:
                with open(self.stats_file, "r", encoding="utf-8") as f:
                    self.domain_stats = json.load(f)
            except Exception:
                self.domain_stats = {}

    def save_stats(self):
        with open(self.stats_file, "w", encoding="utf-8") as f:
            json.dump(self.domain_stats, f, indent=2)

    def update_domain_reputation(self, domain, relevant):
        """Update domain performance after each page"""
        if domain not in self.domain_stats:
            self.domain_stats[domain] = {"pages": 0, "relevant": 0, "relevance_ratio": 0}

        d = self.domain_stats[domain]
        d["pages"] += 1
        if relevant:
            d["relevant"] += 1
        d["relevance_ratio"] = round(d["relevant"] / d["pages"], 2)

    # -----------------------------
    # Adaptive control (live tuning)
    # -----------------------------
    def record_latency(self, latency):
        # Smooth average latency for tuning
        prev = self.run_metrics["avg_latency"]
        self.run_metrics["avg_latency"] = (prev * 0.9) + (latency * 0.1)

    def record_page(self, relevant):
        self.run_metrics["pages"] += 1
        if relevant:
            self.run_metrics["relevant"] += 1

    def tune(self, logger=None):
        """Adjust depth and delay dynamically"""
        pages = self.run_metrics["pages"]
        if pages < 10:
            return  # not enough data yet

        good_ratio = self.run_metrics["relevant"] / max(pages, 1)
        avg_latency = self.run_metrics["avg_latency"]

        # --- Adaptive depth tuning ---
        if good_ratio < 0.3:
            self.run_metrics["depth_limit"] = max(2, self.run_metrics["depth_limit"] - 1)
        elif good_ratio > 0.6:
            self.run_metrics["depth_limit"] = min(6, self.run_metrics["depth_limit"] + 1)

        # --- Adaptive delay tuning ---
        if avg_latency > 8.0:
            self.run_metrics["download_delay"] = min(5.0, self.run_metrics["download_delay"] + 0.5)
        elif avg_latency < 3.0:
            self.run_metrics["download_delay"] = max(0.5, self.run_metrics["download_delay"] - 0.2)

        if logger:
            logger.info(
                f"[ADAPT] depth={self.run_metrics['depth_limit']} delay={self.run_metrics['download_delay']:.1f}s good_ratio={good_ratio:.2f} latency={avg_latency:.2f}"
            )
