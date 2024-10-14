from langchain_openai import AzureOpenAIEmbeddings
from typing import List, Dict, Any
import os
import time

class Embed:
    def __init__(self, deployment: str = "text-embedding-ada-002"):
        self.embeddings = AzureOpenAIEmbeddings(
            deployment=deployment,
            azure_endpoint=os.getenv("EMBEDDER_OPENAI_API_BASE"),
            api_key=os.getenv("EMBEDDER_OPENAI_API_KEY"),
            api_version=os.getenv("EMBEDDER_OPENAI_API_VERSION"),
            chunk_size=1
        )
        self.request_count = 0
        self.last_request_time = time.time()
        self.max_requests_per_minute = 720

    def embed_documents(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """
        Embed a list of document chunks.
        
        :param documents: List of document dictionaries, each containing 'page_content' and 'metadata'
        :return: List of document dictionaries with embeddings added
        """
        texts = [doc['page_content'] for doc in documents]
        embedded_documents = []
        for i, text in enumerate(texts):
            self._rate_limit()
            embedding = self.embeddings.embed_documents([text])[0]
            embedded_documents.append({
                'page_content': documents[i]['page_content'],
                'metadata': documents[i]['metadata'],
                'document_name': documents[i]['metadata'].get('source', 'Unknown'),  # Add this line
                'page': documents[i]['metadata'].get('page', 'Unknown'),  # Add this line
                'chunk': documents[i]['metadata'].get('chunk', 'Unknown'),  # Add this line
                'embedding': embedding,
            })
        
        return embedded_documents

    def _rate_limit(self):
        """Implement rate limiting to not exceed 720 requests per minute."""
        current_time = time.time()
        if current_time - self.last_request_time >= 60:
            self.request_count = 0
            self.last_request_time = current_time

        if self.request_count >= self.max_requests_per_minute:
            sleep_time = 60 - (current_time - self.last_request_time)
            if sleep_time > 0:
                time.sleep(sleep_time)
            self.request_count = 0
            self.last_request_time = time.time()

        self.request_count += 1

    def set_deployment(self, deployment: str):
        """Update the embedding model deployment."""
        self.embeddings = AzureOpenAIEmbeddings(
            deployment=deployment,
            azure_endpoint=os.getenv("EMBEDDER_OPENAI_API_BASE"),
            api_key=os.getenv("EMBEDDER_OPENAI_API_KEY"),
            api_version=os.getenv("EMBEDDER_OPENAI_API_VERSION"),
            chunk_size=1
        )