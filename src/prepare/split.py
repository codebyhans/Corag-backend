from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import List, Dict, Any

class Split:
    def __init__(self, chunk_size: int = 1000, chunk_overlap: int = 200):
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            length_function=len,
        )

    def split_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Split a list of documents into chunks.
        
        :param documents: List of document dictionaries, each containing 'page_content' and 'metadata'
        :return: List of chunked document dictionaries
        """
        chunked_documents = []
        for doc in documents:
            splits = self.text_splitter.split_text(doc.page_content)
            for i, split in enumerate(splits):
                chunked_documents.append({
                    'page_content': split,
                    'metadata': {**doc.metadata, 'chunk': i}
                })
        return chunked_documents

    def set_chunk_size(self, chunk_size: int):
        """Update the chunk size of the text splitter."""
        self.text_splitter.chunk_size = chunk_size

    def set_chunk_overlap(self, chunk_overlap: int):
        """Update the chunk overlap of the text splitter."""
        self.text_splitter.chunk_overlap = chunk_overlap