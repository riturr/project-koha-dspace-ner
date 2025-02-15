from pathlib import Path

from pandas import DataFrame
import pandas as pd
import os
import lxml.etree as ET
import logging
from tqdm import tqdm

from registration_asistant_ner.training_data.pdf_reader import get_text_from_page

logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    level=logging.INFO,
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)

tqdm.pandas()

def parse_xml(xml_file: Path) -> dict :
    """
    Parse the XML file to extract the metadata.
    """
    if not os.path.exists(xml_file):
        logger.warning(f"XML file '{xml_file}' not found.")
        return {
            'title': '',
            'abstract': '',
            'subjects': [],
            'authors': [],
            'advisors': [],
            'issued': '',
        }

    root = ET.parse(xml_file, parser=ET.XMLParser(recover=True))

    title = root.xpath('/mets:METS/mets:dmdSec/mets:mdWrap/mets:xmlData/dim:dim/dim:field[@element="title"]/text()',
                       namespaces={'mets': 'http://www.loc.gov/METS/', 'dim': 'http://www.dspace.org/xmlns/dspace/dim'})
    abstract = root.xpath(
        '/mets:METS/mets:dmdSec/mets:mdWrap/mets:xmlData/dim:dim/dim:field[@element="description"]/text()',
        namespaces={'mets': 'http://www.loc.gov/METS/', 'dim': 'http://www.dspace.org/xmlns/dspace/dim'})
    subjects = root.xpath(
        '/mets:METS/mets:dmdSec/mets:mdWrap/mets:xmlData/dim:dim/dim:field[@element="subject"]/text()',
        namespaces={'mets': 'http://www.loc.gov/METS/', 'dim': 'http://www.dspace.org/xmlns/dspace/dim'})
    authors = root.xpath(
        '/mets:METS/mets:dmdSec/mets:mdWrap/mets:xmlData/dim:dim/dim:field[@element="contributor" and @qualifier="author"]/text()',
        namespaces={'mets': 'http://www.loc.gov/METS/', 'dim': 'http://www.dspace.org/xmlns/dspace/dim'})
    advisors = root.xpath(
        '/mets:METS/mets:dmdSec/mets:mdWrap/mets:xmlData/dim:dim/dim:field[@element="contributor" and @qualifier="advisor"]/text()',
        namespaces={'mets': 'http://www.loc.gov/METS/', 'dim': 'http://www.dspace.org/xmlns/dspace/dim'})
    issued = root.xpath(
        '/mets:METS/mets:dmdSec/mets:mdWrap/mets:xmlData/dim:dim/dim:field[@element="date" and @qualifier="issued"]/text()',
        namespaces={'mets': 'http://www.loc.gov/METS/', 'dim': 'http://www.dspace.org/xmlns/dspace/dim'})

    return {
        'title': title[0] if len(title) > 0 else '',
        'abstract': abstract[0] if len(abstract) > 0 else '',
        'subjects': subjects,
        'authors': authors,
        'advisors': advisors,
        'issued': issued[0] if len(issued) > 0 else '',
    }


def read_cover_page_text(pdf_file: str, **kwargs) -> str | None:
    """
    Read the text from the cover page of the PDF file.
    """
    if not os.path.exists(pdf_file):
        logger.warning(f"PDF file '{pdf_file}' not found.")
        return None
    try:
        return get_text_from_page(pdf_file, 0, **kwargs)
    except Exception as e:
        logger.error(f"Error reading cover page from '{pdf_file}': {e}")
        return None


def get_file_path(base_folder, files, extension) -> Path | None:
    """
    Get the file path from the list of files. Only returns the first file found.
    """
    for file in files:
        if "url" in file and "path" in file and extension in file["url"]:
            return Path(base_folder) / file["path"]
    return None


def load_scraped_data(index_file, files_path, **kwargs) -> DataFrame:
    """
    Load the scraped data from the `index_file` and the `files_path`.
    """
    if not os.path.exists(index_file):
        raise FileNotFoundError(f"Index file '{index_file}' not found.")

    if not os.path.exists(files_path):
        raise FileNotFoundError(f"Files path '{files_path}' not found.")

    index_df = pd.read_json(index_file, lines=True)

    # Get the full path of the XML and PDF files
    index_df['xml_file'] = index_df['files'].progress_apply(lambda x: get_file_path(files_path, x, '.xml'))
    index_df['pdf_file'] = index_df['files'].progress_apply(lambda x: get_file_path(files_path, x, '.pdf'))

    # Parse the XML file to extract the metadata and add it to the DataFrame
    index_df = index_df.join(index_df['xml_file'].progress_apply(parse_xml).apply(pd.Series))

    # Read the text from the cover page of the PDF file
    tessdata = kwargs.get("tessdata", None)
    index_df['cover_page_text'] = index_df['pdf_file'].progress_apply(read_cover_page_text, tessdata=tessdata)

    logger.info(f"Loaded {len(index_df)} records from '{index_file}'.")

    return index_df

