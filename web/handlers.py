"""
Request Handlers Module
-----------------------
Business logic for handling incoming requests.
Coordinates between web layer and AWS-native services.
"""

import logging
from typing import Dict, Any

from services.conversation_engine import create_conversation_engine, IntelligentResponder
from config.settings import get_settings

logger = logging.getLogger(__name__)


class ChatHandler:
    """
    Handles chat-related requests and coordinates with conversation engine.
    Uses AWS Bedrock for LLM and OpenSearch for retrieval.
    """

    def __init__(self) -> None:
        """Initialize the chat handler with AWS-native conversation engine."""
        settings = get_settings()
        
        logger.info("Initializing chat handler with AWS services...")
        
        self._responder = create_conversation_engine(
            index_name=settings.database.index_name,
            model=settings.llm.model_name
        )
        
        logger.info("Chat handler ready (AWS Bedrock + OpenSearch)")

    def handle_user_message(self, message: str) -> Dict[str, Any]:
        """
        Process a user message and generate a response.

        Args:
            message: User's input message.

        Returns:
            Dictionary with answer and success status.
        """
        try:
            answer = self._responder.generate_response(message)
            
            return {
                "success": True,
                "answer": answer,
                "message_received": message
            }
            
        except Exception as error:
            logger.error(f"Error handling message: {error}")
            
            return {
                "success": False,
                "answer": self._generate_error_response(),
                "error": str(error)
            }

    def handle_detailed_query(self, message: str) -> Dict[str, Any]:
        """
        Process a query and return detailed response with sources.

        Args:
            message: User's query.

        Returns:
            Detailed response including context information.
        """
        try:
            detailed_response = self._responder.get_detailed_response(message)
            
            # Format context for JSON serialization
            context_summary = []
            for doc in detailed_response.get("context", []):
                context_summary.append({
                    "content_preview": doc.page_content[:200] + "...",
                    "source": doc.metadata.get("origin", "unknown")
                })
            
            return {
                "success": True,
                "answer": detailed_response["answer"],
                "sources": context_summary,
                "query": message
            }
            
        except Exception as error:
            logger.error(f"Error in detailed query: {error}")
            
            return {
                "success": False,
                "answer": self._generate_error_response(),
                "sources": [],
                "error": str(error)
            }

    def _generate_error_response(self) -> str:
        """Generate a user-friendly error message."""
        return (
            "I apologize, but I encountered an issue processing your request. "
            "Please try again, or rephrase your question."
        )


class InputValidator:
    """Validates and sanitizes user input."""

    MAX_MESSAGE_LENGTH = 2000
    MIN_MESSAGE_LENGTH = 1

    @classmethod
    def validate_message(cls, message: str) -> tuple:
        """
        Validate a user message.

        Args:
            message: Raw user input.

        Returns:
            Tuple of (is_valid, error_message or None).
        """
        if not message or len(message.strip()) < cls.MIN_MESSAGE_LENGTH:
            return False, "Message cannot be empty"
        
        if len(message) > cls.MAX_MESSAGE_LENGTH:
            return False, f"Message exceeds maximum length of {cls.MAX_MESSAGE_LENGTH}"
        
        return True, None

    @classmethod
    def sanitize_message(cls, message: str) -> str:
        """
        Clean and prepare user message for processing.

        Args:
            message: Raw user input.

        Returns:
            Sanitized message string.
        """
        return message.strip()
