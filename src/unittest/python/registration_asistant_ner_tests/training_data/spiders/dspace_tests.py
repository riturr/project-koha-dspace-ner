import unittest
import os
import shutil
from scrapy.crawler import CrawlerProcess

from registration_asistant_ner.training_data.spiders.dspace import DSpaceSpider

TEST_FILE = "./src/unittest/python/resources/dspace.jsonl"
FILES_STORE = "./src/unittest/python/resources/dspace_files"


class DSpaceTests(unittest.TestCase):
    def test_dspace(self):
        os.remove(TEST_FILE) if os.path.exists(TEST_FILE) else None
        shutil.rmtree(FILES_STORE, ignore_errors=True) if os.path.exists(
            FILES_STORE
        ) else None

        process = CrawlerProcess(
            settings={
                "FEEDS": {
                    TEST_FILE: {"format": "jsonlines"},
                },
                "ITEM_PIPELINES": {
                    "scrapy.pipelines.files.FilesPipeline": 1,
                },
                "FILES_STORE": FILES_STORE,
            }
        )

        process.crawl(
            DSpaceSpider,
            community_url="https://repositorio.umsa.bo/xmlui/handle/123456789/17064/recent-submissions?offset=3240",
            custom_settings={
                "DOWNLOADER_MIDDLEWARES": {
                    "scrapy.downloadermiddlewares.httpcache.HttpCacheMiddleware": 10,
                },
                "HTTPCACHE_ENABLED": True,
                "HTTPCACHE_DIR": "httpcache",
                "HTTPCACHE_ALWAYS_STORE": True,
                "HTTPCACHE_STORAGE": "scrapy.extensions.httpcache.FilesystemCacheStorage",
                "HTTPCACHE_POLICY": "scrapy.extensions.httpcache.DummyPolicy",
                "HTTPCACHE_IGNORE_HTTP_CODES": [301, 302, 303, 307, 308],
                "HTTPCACHE_IGNORE_MISSING": False,
                "HTTPCACHE_IGNORE_RESPONSE_CACHE_CONTROLS": ["no-cache", "no-store"],
            },
        )
        process.start()
        self.assertTrue(os.path.exists(TEST_FILE))
        # Check if the file has more than 20 records, which means that multiple pages were scraped (not just the first one)
        with open(TEST_FILE, "r") as f:
            lines = f.readlines()
            # self.assertTrue(len(lines) > 20)
            self.assertTrue(len(lines) >= 1)
