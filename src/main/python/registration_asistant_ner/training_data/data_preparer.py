import re

from pandas import DataFrame, Series
import unidecode
from spacy.tokens.doc import Doc
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def correct_data(value: str) -> str:
    """
    Correct the data.
    """

    # Remove leading/trailing whitespaces
    value = value.strip()

    # Remove consecutive whitespaces
    value = ' '.join(value.split())

    # Remove carriage return and line feed characters
    value = value.replace("\r", "").replace("\n", "")

    # Unidecode the text
    value = unidecode.unidecode(value)

    return value


def correct_cover_page_text(text: str) -> str:
    """
    Correct the text from the cover page.
    """
    # Remove leading/trailing and consecutive whitespaces
    text = "\n".join([" ".join(line.split()).strip() for line in text.split("\n")])

    # Remove carriage return
    text = text.replace("\r", "")

    # Unidecode the text
    text = unidecode.unidecode(text)

    return text


def upper_case(value: str) -> str:
    """
    Upper case the data.
    """
    return value.upper()


def permute_names(names: list[str]) -> list[str]:
    """
    Generate permutations of the names. For example, ['Doe, John'] -> ['John Doe', 'Doe John']
    This is done because the names could be written in different orders on the documents.
    """
    permuted_names = []
    for name in names:
        parts = name.split(",")

        # only take the first two parts (first name and last name)
        parts = parts[:2]
        parts = [part.strip() for part in parts]

        # generate permutations
        name_1 = " ".join(parts)
        name_2 = " ".join(reversed(parts))

        permuted_names.append(name_1)
        
        # only add the second name if it is different from the first name
        # (to avoid duplicates, this could happen if the name has only one part)
        if name_1 != name_2:
            permuted_names.append(name_2)

    return permuted_names


def prepare_data(data: DataFrame) -> DataFrame:
    """
    Prepare the data.
    """
    # Remove rows with missing cover page text
    data = data.dropna(subset=['cover_page_text'])

    # Correct the data
    data['title'] = data['title'].apply(correct_data).apply(upper_case)
    data['abstract'] = data['abstract'].apply(correct_data).apply(upper_case)
    data['subjects'] = data['subjects'].apply(lambda x: [upper_case(correct_data(value)) for value in x])
    data['authors'] = data['authors'].apply(lambda x: [upper_case(correct_data(value)) for value in x])
    data['advisors'] = data['advisors'].apply(lambda x: [upper_case(correct_data(value)) for value in x])
    data['issued'] = data['issued'].apply(correct_data).apply(upper_case)
    data['cover_page_text'] = data['cover_page_text'].apply(correct_cover_page_text).apply(upper_case)

    # Filter out the rows to only keep the ones with issued date >= 2010. This is to avoid training with old data.
    # Missing dates are set to 0 so they will be filtered out.
    data['year'] = data['issued'].apply(lambda x: int(re.search(r'\d{4}', x).group(0)) if re.search(r'\d{4}', x) else 0)
    data = data[data['year'] >= 2010]

    # Filter data based on the document type
    DOCUMENTS_TYPES_TO_KEEP = [
    'Proyectos de Grado',
    'Tesis de Grado',
    'Tesis',
    'Trabajo Dirigido',
    'Proyecto de Grado',
    'Tesis de Especialidad',
    'Tesis de Maestría',
    'Trabajos Dirigidos',
    'PETAENG',
    'Trabajos dirigidos'
    ]
    data['document_type'] = data['breadcrumb'].apply(lambda b: b[-2])
    data = data[data['document_type'].isin(DOCUMENTS_TYPES_TO_KEEP)]

    # Generate permutations of the names
    data['authors'] = data['authors'].apply(permute_names)
    data['advisors'] = data['advisors'].apply(permute_names)

    return data

import spacy
# nlp = spacy.blank("es")
nlp = spacy.load("es_core_news_lg")


def build_matcher_pattern(text: str) -> str:
    """
    Build a regex pattern from the text.
    For example if the text is 'John Doe', the pattern will be match 'John Doe', 'John\nDoe'
    """
    parts = text.split(" ")
    pattern = ""
    for part in parts:
        pattern += f"{re.escape(part)}[\\s\n]*"

    # remove the last [\s\n]* from the pattern to avoid matching a whitespace at the end of the text
    pattern = pattern[:-6] if len(pattern) > 6 else pattern
    return pattern


def generate_doc_with_entities(row: dict, main_text_column: str, columns_to_match: list[str]) -> Doc:
    """
    Generate a Doc object with the entities from the columns to match.
    For example, if the main text column is 'text' and the columns to match are ['authors', 'advisors'],
    the function will generate a Doc object with the entities for the authors and advisors in the text column.

    :param row: Row with the data.
    :param main_text_column: Name of the main text column.
    :param columns_to_match: List of columns to match.
    :return: Doc object with the entities
    """
    doc = nlp(row[main_text_column])
    spans = []
    for column in columns_to_match:
        assert column in row, f"Column '{column}' not found in the row."

        if not row[column]:
            continue

        if not isinstance(row[column], list):
            field = [row[column]]
        else:
            field = row[column]

        for value in field:
            pattern = build_matcher_pattern(value)
            matches = re.compile(pattern).finditer(row[main_text_column])
            for match in matches:
                start, end = match.span()
                label = column.upper()  # use the column name as the label for the entity
                span = doc.char_span(start, end, label)
                if span is not None:
                    spans.append(span)
    doc.set_ents(spans)
    return doc


# TODO: Add unit tests for this function
def generate_training_data(data: DataFrame, from_columns: list[str]) -> Series:
    """
    Generate the training data with the entities.

    :param data: pandas DataFrame with the data. The DataFrame should have the columns 'cover_page_text' and the
    columns given in the 'from_columns' parameter. The 'cover_page_text' column should have the text from the cover
    page of the document. The data should have been prepared with the 'prepare_data' function.
    :param from_columns: List of columns to match. The entities will be extracted from these columns.
    :return: pandas Series with the Doc objects.
    """
    training_df: Series = data.apply(
        lambda row: generate_doc_with_entities(row, 'cover_page_text', ['authors', 'advisors']),
        axis=1,
        result_type='reduce'
    )
    # filter out the rows with no entities
    filtered_training_df = training_df.where(training_df.apply(lambda x: len(x.ents) > 0), other=None).dropna()

    logger.info(f"Generated training data with {len(filtered_training_df)} documents.")
    return filtered_training_df