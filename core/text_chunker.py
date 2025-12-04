"""
Text Chunker Module
-------------------
Provides intelligent text segmentation for optimal embedding generation.
Splits large documents into digestible chunks while preserving context.
"""

import logging
from dataclasses import dataclass
from typing import List

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.schema import Document

logger = logging.getLogger(__name__)


@dataclass
class ChunkingConfig:
    """Configuration parameters for text chunking."""
    
    segment_size: int = 500
    overlap_size: int = 50
    length_function: str = "character"


class TextSegmenter:
    """
    Handles the segmentation of documents into smaller, 
    embedding-friendly chunks.
    """

    def __init__(self, config: ChunkingConfig = None) -> None:
        """
        Initialize the text segmenter with optional configuration.

        Args:
            config: Chunking configuration. Uses defaults if not provided.
        """
        self._config = config or ChunkingConfig()
        self._splitter = self._create_splitter()

    def _create_splitter(self) -> RecursiveCharacterTextSplitter:
        """Build the underlying text splitter with current configuration."""
        return RecursiveCharacterTextSplitter(
            chunk_size=self._config.segment_size,
            chunk_overlap=self._config.overlap_size
        )

    def segment_documents(self, documents: List[Document]) -> List[Document]:
        """
        Split documents into smaller chunks suitable for embedding.

        Args:
            documents: List of documents to segment.

        Returns:
            List of chunked Document objects.
        """
        if not documents:
            logger.warning("No documents provided for segmentation")
            return []

        segmented = self._splitter.split_documents(documents)
        
        logger.info(
            f"Segmented {len(documents)} documents into {len(segmented)} chunks"
        )
        
        return segmented

    def update_configuration(self, new_config: ChunkingConfig) -> None:
        """
        Update chunking configuration and rebuild the splitter.

        Args:
            new_config: New configuration to apply.
        """
        self._config = new_config
        self._splitter = self._create_splitter()
        logger.debug(f"Updated chunking config: size={new_config.segment_size}")


def create_text_segments(
    documents: List[Document],
    segment_size: int = 500,
    overlap: int = 50
) -> List[Document]:
    """
    Convenience function for quick document segmentation.

    Args:
        documents: Documents to segment.
        segment_size: Target size for each chunk.
        overlap: Number of characters to overlap between chunks.

    Returns:
        List of segmented Document objects.
    """
    config = ChunkingConfig(segment_size=segment_size, overlap_size=overlap)
    segmenter = TextSegmenter(config)
    return segmenter.segment_documents(documents)
