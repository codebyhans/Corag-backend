from langchain_community.document_loaders import (
    PyPDFLoader,
    TextLoader,
    CSVLoader,
    UnstructuredWordDocumentLoader,
    UnstructuredPowerPointLoader,
    UnstructuredExcelLoader
)
from typing import List

class Load:
    def __init__(self):
        self.loaders = {
            'pdf': PyPDFLoader,
            'txt': TextLoader,
            'csv': CSVLoader,
            'doc': UnstructuredWordDocumentLoader,
            'docx': UnstructuredWordDocumentLoader,
            'ppt': UnstructuredPowerPointLoader,
            'pptx': UnstructuredPowerPointLoader,
            'xls': UnstructuredExcelLoader,
            'xlsx': UnstructuredExcelLoader
        }

    def load_document(self, file_path: str) -> List:
        file_extension = file_path.split('.')[-1].lower()
        if file_extension not in self.loaders:
            raise ValueError(f"Unsupported file type: {file_extension}")

        loader = self.loaders[file_extension](file_path)
        return loader.load()

    def add_loader(self, file_extension: str, loader_class):
        self.loaders[file_extension.lower()] = loader_class