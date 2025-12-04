"""
Document Processor Module
-------------------------
Handles loading and extraction of content from PDF documents.
Provides a clean interface for ingesting knowledge base materials.
"""

import logging
from pathlib import Path
from typing import List, Optional

from langchain_community.document_loaders import PyPDFLoader, DirectoryLoader
from langchain.schema import Document

logger = logging.getLogger(__name__)


class DocumentLoader:
    """
    Responsible for loading documents from various sources.
    Currently supports PDF files from directories.
    """

    def __init__(self, source_directory: str) -> None:
        """
        Initialize the document loader with a source directory.

        Args:
            source_directory: Path to the directory containing documents.
        """
        self._source_path = Path(source_directory)
        self._validate_source()

    def _validate_source(self) -> None:
        """Ensure the source directory exists and is accessible."""
        if not self._source_path.exists():
            raise FileNotFoundError(
                f"Knowledge base directory not found: {self._source_path}"
            )
        if not self._source_path.is_dir():
            raise NotADirectoryError(
                f"Expected directory but found file: {self._source_path}"
            )

    def extract_all_documents(self, file_pattern: str = "*.pdf") -> List[Document]:
        """
        Extract content from all matching documents in the source directory.

        Args:
            file_pattern: Glob pattern for file matching. Defaults to PDF files.

        Returns:
            List of Document objects containing extracted content.
        """
        logger.info(f"Loading documents from: {self._source_path}")
        
        directory_reader = DirectoryLoader(
            path=str(self._source_path),
            glob=file_pattern,
            loader_cls=PyPDFLoader
        )
        
        extracted_docs = directory_reader.load()
        logger.info(f"Successfully loaded {len(extracted_docs)} document pages")
        
        return extracted_docs

    def sanitize_metadata(self, documents: List[Document]) -> List[Document]:
        """
        Clean document metadata to retain only essential information.

        Args:
            documents: List of documents with potentially verbose metadata.

        Returns:
            Documents with streamlined metadata containing only source info.
        """
        cleaned_documents: List[Document] = []
        
        for doc in documents:
            origin_path = doc.metadata.get("source", "unknown")
            cleaned_doc = Document(
                page_content=doc.page_content,
                metadata={"origin": origin_path}
            )
            cleaned_documents.append(cleaned_doc)
        
        logger.debug(f"Sanitized metadata for {len(cleaned_documents)} documents")
        return cleaned_documents


def load_knowledge_base(directory_path: str) -> List[Document]:
    """
    Convenience function to load and prepare documents from a directory.

    Args:
        directory_path: Path to the knowledge base directory.

    Returns:
        List of processed Document objects ready for embedding.
    """
    loader = DocumentLoader(directory_path)
    raw_documents = loader.extract_all_documents()
    prepared_documents = loader.sanitize_metadata(raw_documents)
    return prepared_documents
