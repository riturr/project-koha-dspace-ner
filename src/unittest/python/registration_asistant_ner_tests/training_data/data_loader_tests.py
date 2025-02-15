import unittest
from registration_asistant_ner.training_data.data_loader import load_scraped_data
from pathlib import Path


class GeneratorTests(unittest.TestCase):
    def test_load_scraped_data(self):
        tessdata = Path(__file__).parent / "resources" / "tessdata"

        index_file = Path(__file__).parent / "resources" / "all_collected_data.jsonl"
        # files_path = Path(__file__).parent / "resources" / "dspace_files"
        files_path = Path("D:\\dspace-files\\files")

        df = load_scraped_data(index_file, files_path, tessdata=str(tessdata))
        print(df.to_string())
        self.assertIsNotNone(df)
        self.assertTrue(len(df) > 0)
        self.assertTrue("title" in df.columns)
        self.assertTrue("abstract" in df.columns)
        self.assertTrue("subjects" in df.columns)
        self.assertTrue("authors" in df.columns)
        self.assertTrue("advisors" in df.columns)
        self.assertTrue("issued" in df.columns)
        self.assertTrue("xml_file" in df.columns)
        self.assertTrue("pdf_file" in df.columns)

