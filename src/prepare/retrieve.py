from azure.cosmos import CosmosClient, PartitionKey
from typing import List, Dict, Any
import hashlib
import os
import time
import numpy as np
import datetime as dt

class Retrieve:
    def __init__(self):
        cosmos_endpoint = os.getenv("COSMOS_ENDPOINT")
        cosmos_key = os.getenv("COSMOS_KEY")
        database_name = os.getenv("COSMOS_DATABASE_NAME")
        container_name = os.getenv("COSMOS_CONTAINER_NAME")

        client = CosmosClient(cosmos_endpoint, cosmos_key)
        self.database = client.create_database_if_not_exists(id=database_name)
        self.container = self.database.create_container_if_not_exists(
            id=container_name, 
            partition_key=PartitionKey(path="/passphrase_hash")
        )
        self.max_ru_per_second = 1000
        self.last_request_time = time.time()
        self.consumed_ru = 0
        self.default_ru = 5.0

    def _hash_passphrase(self, passphrase: str) -> str:
        return hashlib.sha256(passphrase.encode()).hexdigest()

    def _rate_limit(self, consumed_ru: float):
        self.consumed_ru += consumed_ru
        current_time = time.time()
        elapsed_time = current_time - self.last_request_time

        if elapsed_time < 1 and self.consumed_ru > self.max_ru_per_second:
            sleep_time = 1 - elapsed_time
            time.sleep(sleep_time)
            self.consumed_ru = 0
            self.last_request_time = time.time()
        elif elapsed_time >= 1:
            self.consumed_ru = 0
            self.last_request_time = current_time

    def vector_search(self, passphrase: str, query_vector: List[float], top_k: int = 10) -> List[Dict[str, Any]]:
        passphrase_hash = self._hash_passphrase(passphrase)
        query_vector_str = str(query_vector).replace('[', '').replace(']', '')
        print('******')
        print('pass: ', passphrase)
        print('hash: ', passphrase_hash)
        query = f"""
        SELECT TOP {top_k} 
            c.content, 
            c.document_name, 
            c.page, 
            VectorDistance(c.embedding, [{query_vector_str}]) AS similarity_score
        FROM c
        WHERE c.passphrase_hash = '{passphrase_hash}'
        AND VectorDistance(c.embedding, [{query_vector_str}]) > 0.65
        AND c.keep_until > '{dt.datetime.now().isoformat()}'
        ORDER BY VectorDistance(c.embedding, [{query_vector_str}])
        """
        print(query)
        
        items = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        for item in items:
            self._rate_limit(self.default_ru)  
        
        return items

    def delete_embeddings(self, passphrase: str):
        passphrase_hash = self._hash_passphrase(passphrase)
        query = f"SELECT * FROM c WHERE c.passphrase_hash = '{passphrase_hash}'"
        items = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        for item in items:
            self.container.delete_item(item=item['id'], partition_key=passphrase_hash)
            self._rate_limit(self.default_ru)  # Assume a fixed request charge for delete operations
