"""
Embedding Service Module
------------------------
Provides vector embedding generation using transformer models.
Wraps HuggingFace sentence transformers for semantic representation.
"""

import logging
from typing import List, Optional

from langchain_community.embeddings import HuggingFaceEmbeddings

logger = logging.getLogger(__name__)


class EmbeddingGenerator:
    """
    Generates vector embeddings for text using pre-trained models.
    Uses lazy initialization for efficient resource management.
    """

    # Default model produces 384-dimensional vectors
    DEFAULT_MODEL = "sentence-transformers/all-MiniLM-L6-v2"
    VECTOR_DIMENSIONS = 384

    _instance: Optional["EmbeddingGenerator"] = None
    _embeddings_model: Optional[HuggingFaceEmbeddings] = None

    def __new__(cls, model_identifier: str = None):
        """Implement singleton pattern for resource efficiency."""
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance

    def __init__(self, model_identifier: str = None) -> None:
        """
        Initialize the embedding generator.

        Args:
            model_identifier: HuggingFace model name. Uses default if not specified.
        """
        if self._initialized:
            return
            
        self._model_name = model_identifier or self.DEFAULT_MODEL
        self._embeddings_model = None
        self._initialized = True

    def _ensure_model_loaded(self) -> None:
        """Lazily load the embedding model on first use."""
        if self._embeddings_model is None:
            logger.info(f"Initializing embedding model: {self._model_name}")
            self._embeddings_model = HuggingFaceEmbeddings(
                model_name=self._model_name
            )
            logger.info("Embedding model ready")

    def get_embeddings_interface(self) -> HuggingFaceEmbeddings:
        """
        Get the underlying embeddings interface for integration with vector stores.

        Returns:
            HuggingFaceEmbeddings instance ready for use.
        """
        self._ensure_model_loaded()
        return self._embeddings_model

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for a single text input.

        Args:
            text: Text to embed.

        Returns:
            List of floats representing the embedding vector.
        """
        self._ensure_model_loaded()
        return self._embeddings_model.embed_query(text)

    def generate_batch_embeddings(self, texts: List[str]) -> List[List[float]]:
        """
        Generate embeddings for multiple texts efficiently.

        Args:
            texts: List of texts to embed.

        Returns:
            List of embedding vectors.
        """
        self._ensure_model_loaded()
        return self._embeddings_model.embed_documents(texts)

    @property
    def dimensions(self) -> int:
        """Return the dimensionality of generated embeddings."""
        return self.VECTOR_DIMENSIONS

    @property
    def model_name(self) -> str:
        """Return the name of the model being used."""
        return self._model_name


def get_embedding_service() -> EmbeddingGenerator:
    """
    Factory function to obtain the embedding service instance.

    Returns:
        Singleton EmbeddingGenerator instance.
    """
    return EmbeddingGenerator()
