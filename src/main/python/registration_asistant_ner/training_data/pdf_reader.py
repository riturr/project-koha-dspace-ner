import os

import pymupdf
from pymupdf import Pixmap, Page
import cv2
import numpy as np
from pytesseract import pytesseract

DPI = 300
AREA_THRESHOLD = DPI * DPI * 0.03


def get_text_from_page(pdf, page_number, **kwargs):
    img_page = get_page_as_image(pdf, page_number)
    img_page = remove_logos_from_page(img_page)
    return get_text_from_image(img_page, **kwargs)


def get_text_from_page_range(pdf, start_page, end_page):
    return "\n".join(get_text_from_page(pdf, page) for page in range(start_page, end_page + 1))


def get_page_as_image(pdf, page_number) -> Pixmap:
    doc = pymupdf.open(pdf)
    page = doc.load_page(page_number)
    return page.get_pixmap(dpi=DPI)


def get_text_from_image(image: Pixmap, **kwargs) -> str:
    if False:
        tessdata = kwargs.get("tessdata", None)
        imgpdf = pymupdf.open("pdf", image.pdfocr_tobytes(language="spa", tessdata=tessdata))
        page: Page = imgpdf[0]
        return page.get_text()
    img = cv2.imdecode(
        np.frombuffer(bytearray(image.tobytes()), dtype=np.uint8), cv2.IMREAD_COLOR
    )
    pytesseract_path = os.getenv("TESSERACT_PATH")
    if pytesseract_path:
        pytesseract.tesseract_cmd = pytesseract_path
    return pytesseract.image_to_string(img, lang="spa")


def remove_logos_from_page(imagePage: Pixmap):
    img = cv2.imdecode(
        np.frombuffer(bytearray(imagePage.tobytes()), dtype=np.uint8), cv2.IMREAD_COLOR
    )
    gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    _, binary_img = cv2.threshold(
        gray_img, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU
    )
    contours, _ = cv2.findContours(
        binary_img, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE
    )
    for contour in contours:
        area = cv2.contourArea(contour)
        if area > AREA_THRESHOLD:
            cv2.drawContours(img, [contour], -1, (255, 255, 255), cv2.FILLED)
    height, width, _ = img.shape
    return Pixmap(pymupdf.csRGB, width, height, bytearray(img.tobytes()), False)

