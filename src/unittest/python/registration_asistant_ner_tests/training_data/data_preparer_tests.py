import re
import unittest
from textwrap import dedent

from registration_asistant_ner.training_data.data_preparer import correct_data, prepare_data, correct_cover_page_text, \
    build_matcher_pattern, permute_names, generate_doc_with_entities
import pandas as pd


class DataLoaderTests(unittest.TestCase):
    def test_correct_data(self):
        # Prepare
        value = "  This is a   test.  \n\r"

        # Execute
        corrected_value = correct_data(value)

        # Assert
        self.assertEqual(corrected_value, "This is a test.")

    def test_correct_cover_page_text(self):
        # Prepare
        text = "This is a  test. \n\n\n”This is another test.”\n"

        # Execute
        corrected_text = correct_cover_page_text(text)

        # Assert
        self.assertEqual(corrected_text, "This is a test.\n\n\n\"This is another test.\"\n")

    def test_permute_names(self):
        # Arrange
        names = ["Doe, John", "Smith, Alice"]

        # Act
        permuted_names = permute_names(names)

        # Assert
        self.assertEqual(len(permuted_names), 4)
        self.assertTrue("John Doe" in permuted_names)
        self.assertTrue("Doe John" in permuted_names)
        self.assertTrue("Alice Smith" in permuted_names)
        self.assertTrue("Smith Alice" in permuted_names)

    def test_prepare_data(self):
        # Prepare
        df = pd.DataFrame(
            {
                "authors": [
                    ["Doe, John", "Doe, Jane"],
                    ["Smith, Alice", "Smith, Bob"],
                    ["Roe, John", "Roe, Jane"],
                    ["Blow, Joe", "Blow, Jane"],
                    ["Shmoe, Joe", "Shmoe, Jane"],
                ],
                "advisors": [
                    ["Doe, John", "Doe, Jane"],
                    ["Smith, Alice", "Smith, Bob"],
                    ["Roe, John", "Roe, Jane"],
                    ["Blow, Joe", "Blow, Jane"],
                    ["Shmoe, Joe", "Shmoe, Jane"],
                ],
                "title": [
                    "Title 1",
                    "Title 2",
                    "Title 3",
                    "Title 4",
                    "Title 5",
                ],
                "abstract": [
                    "Abstract 1",
                    "Abstract 2",
                    "Abstract 3",
                    "Abstract 4",
                    "Abstract 5",
                ],
                "subjects": [
                    ["Subject 1", "Subject 2"],
                    ["Subject 3", "Subject 4"],
                    ["Subject 5", "Subject 6"],
                    ["Subject 7", "Subject 8"],
                    ["Subject 9", "Subject 10"],
                ],
                "issued": [
                    "2021-01-01",
                    "2021-01-02",
                    "2009-01-01", # This row will be removed because of the year < 2010
                    "",           # This row will be removed because of the missing year
                    "2015-01-01",
                ],
                "cover_page_text": [
                    "Cover page text 1\n\n”Second  line”",
                    "Cover page text 2\n\n”Second  line”",
                    "Cover page text 3\n\n”Second  line”",
                    "Cover page text 4\n\n”Second  line”",
                    "Cover page text 5\n\n”Second  line”",
                ],
                "breadcrumb": [
                    ['DSpace Home', 'Facultad de Tecnología', 'Carrera Electrónica y Telecomunicaciones', 'Proyectos de Grado', 'View Item'],
                    ['DSpace Home', 'Facultad de Tecnología', 'Carrera Electrónica y Telecomunicaciones', 'Proyectos de Grado', 'View Item'],
                    ['DSpace Home', 'Facultad de Tecnología', 'Carrera Electrónica y Telecomunicaciones', 'Proyectos de Grado', 'View Item'],
                    ['DSpace Home', 'Facultad de Tecnología', 'Carrera Electrónica y Telecomunicaciones', 'Proyectos de Grado', 'View Item'],
                    ['DSpace Home', 'Facultad de Tecnología', 'Carrera Electrónica y Telecomunicaciones', 'Revista', 'View Item'], # This row will be removed because of the document type
                ]
            }
        )
        print("Original data:")
        print(df.to_string())

        # Execute
        prepared_df = prepare_data(df)

        # Assert
        print("Prepared data:")
        print(prepared_df.to_string())
        expected_df = pd.DataFrame(
            {
                "authors": [["DOE JOHN", "JOHN DOE", "DOE JANE", "JANE DOE"],
                            ["SMITH ALICE", "ALICE SMITH", "SMITH BOB", "BOB SMITH"]],
                "advisors": [["DOE JOHN", "JOHN DOE", "DOE JANE", "JANE DOE"],
                             ["SMITH ALICE", "ALICE SMITH", "SMITH BOB", "BOB SMITH"]],
                "title": ["TITLE 1", "TITLE 2"],
                "abstract": ["ABSTRACT 1", "ABSTRACT 2"],
                "subjects": [["SUBJECT 1", "SUBJECT 2"], ["SUBJECT 3", "SUBJECT 4"]],
                "issued": ["2021-01-01", "2021-01-02"],
                "cover_page_text": ["COVER PAGE TEXT 1\n\n\"SECOND LINE\"", "COVER PAGE TEXT 2\n\n\"SECOND LINE\""],
                "breadcrumb": [['DSpace Home', 'Facultad de Tecnología', 'Carrera Electrónica y Telecomunicaciones', 'Proyectos de Grado', 'View Item'], ['DSpace Home', 'Facultad de Tecnología', 'Carrera Electrónica y Telecomunicaciones', 'Proyectos de Grado', 'View Item']],
                "year": [2021, 2021],
                "document_type": ["Proyectos de Grado", "Proyectos de Grado"],
            }
        )

        print("Expected data:")
        print(expected_df.to_string())

        pd.testing.assert_frame_equal(prepared_df, expected_df)

    def test_build_matcher_pattern(self):
        # Arrange
        text = "This is a test."

        # Act
        pattern = build_matcher_pattern(text)
        matches_1 = re.compile(pattern).findall("This is a test.")
        matches_2 = re.compile(pattern).findall("This \nis a test.")
        matches_3 = re.compile(pattern).findall("This is a test. ")
        matches_4 = re.compile(pattern).findall(" This is a test.")

        # Assert
        self.assertEqual(len(matches_1), 1)
        self.assertEqual(len(matches_2), 1)
        self.assertEqual(len(matches_3), 1)
        self.assertEqual(len(matches_4), 1)
        self.assertEqual(matches_1[0], "This is a test.")
        self.assertEqual(matches_2[0], "This \nis a test.")
        self.assertEqual(matches_3[0], "This is a test.")
        self.assertEqual(matches_4[0], "This is a test.")

    def test_generate_doc_with_entities(self):
        # Arrange
        row = {
            "text": dedent("""
                Title
                
                Authors:
                John Doe
                Jane Doe
                
                Advisors:
                Alice Smith
                Bob Smith
            """),
            "authors": ["John Doe", "Jane Doe"],
            "advisors": ["Alice Smith", "Bob Smith"],
            "title": "Title",
        }

        # Act
        doc = generate_doc_with_entities(row, "text", ["authors", "advisors", "title"])

        # Assert
        self.assertEqual(len(doc.ents), 5)
        self.assertIn("John Doe", [ent.text for ent in doc.ents])
        self.assertIn("Jane Doe", [ent.text for ent in doc.ents])
        self.assertIn("Alice Smith", [ent.text for ent in doc.ents])
        self.assertIn("Bob Smith", [ent.text for ent in doc.ents])
        self.assertIn("Title", [ent.text for ent in doc.ents])

