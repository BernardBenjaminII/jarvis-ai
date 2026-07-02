from dataclasses import dataclass


@dataclass
class Page:

    document_path: str

    page_number: int

    text: str
