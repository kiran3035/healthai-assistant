"""
Vector Database Service - AWS OpenSearch Serverless
----------------------------------------------------
Manages connections and operations with AWS OpenSearch Serverless.
Provides semantic search capabilities using vector embeddings.
"""

import logging
import os
import time
from typing import List, Optional

import boto3
from opensearchpy import OpenSearch, RequestsHttpConnection
from requests_aws4auth import AWS4Auth
from langchain_community.vectorstores import OpenSearchVectorSearch
from langchain.schema import Document

from core.embedding_service import get_embedding_service

logger = logging.getLogger(__name__)


class KnowledgeStore:
    """
    AWS OpenSearch Serverless wrapper for vector storage and retrieval.
    Uses IAM authentication - no API keys required.
    """

    VECTOR_DIMENSION = 384
    INDEX_SETTINGS = {
        "settings": {
            "index": {
                "knn": True,
                "knn.algo_param.ef_search": 100
            }
        },
        "mappings": {
            "properties": {
                "vector_field": {
                    "type": "knn_vector",
                    "dimension": 384,
                    "method": {
                        "name": "hnsw",
                        "space_type": "cosinesimil",
                        "engine": "nmslib"
                    }
                },
                "text": {"type": "text"},
                "metadata": {"type": "object"}
            }
        }
    }

    def __init__(
        self,
        index_identifier: str,
        opensearch_endpoint: str = None,
        aws_region: str = None
    ) -> None:
        """
        Initialize connection to OpenSearch Serverless.

        Args:
            index_identifier: Name of the vector index.
            opensearch_endpoint: OpenSearch endpoint URL.
            aws_region: AWS region for the service.
        """
        self._index_name = index_identifier
        self._endpoint = opensearch_endpoint or os.getenv("OPENSEARCH_ENDPOINT")
        self._region = aws_region or os.getenv("AWS_REGION", "us-east-1")
        
        if not self._endpoint:
            raise ValueError(
                "OpenSearch endpoint not found. "
                "Set OPENSEARCH_ENDPOINT environment variable."
            )
        
        self._embedding_service = get_embedding_service()
        self._client = self._create_client()
        self._vector_store: Optional[OpenSearchVectorSearch] = None

        logger.info(f"Initialized knowledge store: {self._index_name}")

    def _create_client(self) -> OpenSearch:
        """Create authenticated OpenSearch client using IAM."""
        credentials = boto3.Session().get_credentials()
        
        auth = AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self._region,
            "aoss",  # OpenSearch Serverless service
            session_token=credentials.token
        )
        
        # Clean endpoint URL
        host = self._endpoint.replace("https://", "").replace("http://", "")
        
        return OpenSearch(
            hosts=[{"host": host, "port": 443}],
            http_auth=auth,
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection,
            timeout=30
        )

    def ensure_index_exists(self) -> None:
        """Create the vector index if it doesn't already exist."""
        try:
            if not self._client.indices.exists(index=self._index_name):
                logger.info(f"Creating new vector index: {self._index_name}")
                self._client.indices.create(
                    index=self._index_name,
                    body=self.INDEX_SETTINGS
                )
                # Wait for index to be ready
                time.sleep(5)
                logger.info("Vector index created successfully")
            else:
                logger.debug(f"Index already exists: {self._index_name}")
        except Exception as e:
            logger.error(f"Error creating index: {e}")
            raise

    def index_documents(self, document_chunks: List[Document]) -> None:
        """
        Store document chunks in the vector index.

        Args:
            document_chunks: Pre-processed document chunks to index.
        """
        if not document_chunks:
            logger.warning("No documents provided for indexing")
            return

        self.ensure_index_exists()
        
        logger.info(f"Indexing {len(document_chunks)} document chunks...")
        
        # Create vector store and add documents
        self._vector_store = OpenSearchVectorSearch(
            index_name=self._index_name,
            embedding_function=self._embedding_service.get_embeddings_interface(),
            opensearch_url=f"https://{self._endpoint.replace('https://', '')}",
            http_auth=self._get_aws_auth(),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        
        # Add documents in batches
        batch_size = 100
        for i in range(0, len(document_chunks), batch_size):
            batch = document_chunks[i:i + batch_size]
            texts = [doc.page_content for doc in batch]
            metadatas = [doc.metadata for doc in batch]
            self._vector_store.add_texts(texts=texts, metadatas=metadatas)
            logger.debug(f"Indexed batch {i // batch_size + 1}")
        
        logger.info("Document indexing complete")

    def _get_aws_auth(self):
        """Get AWS4Auth for OpenSearch requests."""
        credentials = boto3.Session().get_credentials()
        return AWS4Auth(
            credentials.access_key,
            credentials.secret_key,
            self._region,
            "aoss",
            session_token=credentials.token
        )

    def connect_to_existing(self) -> OpenSearchVectorSearch:
        """
        Connect to an existing vector index.

        Returns:
            Vector store instance connected to the index.
        """
        self._vector_store = OpenSearchVectorSearch(
            index_name=self._index_name,
            embedding_function=self._embedding_service.get_embeddings_interface(),
            opensearch_url=f"https://{self._endpoint.replace('https://', '')}",
            http_auth=self._get_aws_auth(),
            use_ssl=True,
            verify_certs=True,
            connection_class=RequestsHttpConnection
        )
        
        logger.debug(f"Connected to existing index: {self._index_name}")
        return self._vector_store

    def create_retriever(self, result_count: int = 3):
        """
        Create a retriever for semantic search operations.

        Args:
            result_count: Number of results to return per query.

        Returns:
            Retriever instance for RAG pipelines.
        """
        if self._vector_store is None:
            self.connect_to_existing()
        
        return self._vector_store.as_retriever(
            search_type="similarity",
            search_kwargs={"k": result_count}
        )


def initialize_knowledge_base(
    index_name: str,
    document_chunks: List[Document]
) -> KnowledgeStore:
    """
    One-shot initialization of the knowledge base with documents.

    Args:
        index_name: Name for the vector index.
        document_chunks: Documents to store.

    Returns:
        Configured KnowledgeStore instance.
    """
    store = KnowledgeStore(index_name)
    store.index_documents(document_chunks)
    return store
