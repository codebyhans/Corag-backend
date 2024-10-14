from azure.cosmos import CosmosClient, PartitionKey
from typing import List, Dict, Any
import hashlib
import os
import uuid
import time
import datetime as dt

class Store:
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
        self.assumed_request_charge = 1.0  # This value may need adjustment based on actual usage patterns

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

    def store_embeddings(self, passphrase: str, documents: List[Dict[str, Any]], keep_until=None):
        if keep_until is None:
            keep_until = dt.datetime.now() + dt.timedelta(hours=6)

        passphrase_hash = self._hash_passphrase(passphrase)
        for doc in documents:
            item = {
                'id': str(uuid.uuid4()),
                'passphrase_hash': passphrase_hash,
                'metadata': doc['metadata'],
                'embedding': doc['embedding'],
                'document_name': doc['document_name'],  # Add this line
                'page': doc['page'],  # Add this line
                'chunk': doc['chunk'],  # Add this line
                'keep_until': keep_until.isoformat(),
                'load_time': dt.datetime.now().isoformat(),
                'content': doc['page_content'],
                
            }
            response = self.container.upsert_item(item)
            # Assume a fixed request charge for upsert operations
            self._rate_limit(self.assumed_request_charge)

    def get_documents(self, passphrase: str) -> List[Dict[str, Any]]:
        passphrase_hash = self._hash_passphrase(passphrase)
        query = f"""
            SELECT DISTINCT 
                c.document_name
            FROM c WHERE c.passphrase_hash = '{passphrase_hash}'
            """
        print(query)
        items = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True,
            max_item_count=1
        ))
        
        if items:
            return items
        return None

    def delete_embeddings(self, passphrase: str):
        passphrase_hash = self._hash_passphrase(passphrase)
        response = self.container.delete_item(item=passphrase_hash, partition_key=passphrase_hash)

    def delete_documents_older_than(self, current_time, passphrase: str=None):
        # Format current_time to ISO format for the query
        current_time_str = current_time.isoformat()
        query_parts = []
        query_parts.append(f"SELECT c.id FROM c WHERE '{current_time_str}' > c.keep_until")
        if passphrase:
            passphrase_hash = self._hash_passphrase(passphrase)
            query_parts.append(f"""AND c.passphrase_hash = '{passphrase_hash}'""")
        
        query = " ".join(query_parts)
        
        items = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        print('='*100)
        print(items)
        
        for item in items:
            self.container.delete_item(item=item['id'], partition_key=item['id'])  # Use item['passphrase_hash']

    def delete_document(self, passphrase, filename ):
        # Format current_time to ISO format for the query
        passphrase_hash = self._hash_passphrase(passphrase)
        query = f"SELECT c.id FROM c WHERE c.passphrase_hash = '{passphrase_hash}' and c.document_name = '{filename}'"
        items = list(self.container.query_items(
            query=query,
            enable_cross_partition_query=True
        ))
        
        for item in items:
            self.container.delete_item(item=item['id'], partition_key=item['id'])  # Fixed partition key
