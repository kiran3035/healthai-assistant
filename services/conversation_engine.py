"""
Conversation Engine Module - AWS Bedrock
-----------------------------------------
Implements the RAG pipeline using Amazon Bedrock.
Orchestrates retrieval and response generation for user queries.
"""

import logging
import os
from typing import Dict, Any, Optional

import boto3
from langchain_aws import ChatBedrock
from langchain.chains import create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.prompts import ChatPromptTemplate

from services.vector_database import KnowledgeStore
from config.prompts import ASSISTANT_SYSTEM_PROMPT

logger = logging.getLogger(__name__)


class IntelligentResponder:
    """
    Handles the complete RAG pipeline using AWS Bedrock.
    No external API keys required - uses IAM authentication.
    """

    # Available Bedrock models
    BEDROCK_MODELS = {
        "claude-3-sonnet": "anthropic.claude-3-sonnet-20240229-v1:0",
        "claude-3-haiku": "anthropic.claude-3-haiku-20240307-v1:0",
        "claude-instant": "anthropic.claude-instant-v1",
        "titan-text": "amazon.titan-text-express-v1",
        "llama2": "meta.llama2-70b-chat-v1"
    }
    
    DEFAULT_MODEL = "claude-3-sonnet"
    DEFAULT_TEMPERATURE = 0.7

    def __init__(
        self,
        knowledge_store: KnowledgeStore,
        model_name: str = None,
        aws_region: str = None
    ) -> None:
        """
        Initialize the conversation engine with Bedrock.

        Args:
            knowledge_store: Connected knowledge store for retrieval.
            model_name: Bedrock model identifier. Defaults to Claude 3 Sonnet.
            aws_region: AWS region for Bedrock. Uses env var if not provided.
        """
        self._knowledge_store = knowledge_store
        self._region = aws_region or os.getenv("AWS_REGION", "us-east-1")
        
        # Resolve model name
        model_key = model_name or self.DEFAULT_MODEL
        self._model_id = self.BEDROCK_MODELS.get(model_key, model_key)
        
        self._llm = self._initialize_bedrock_client()
        self._chain = self._build_rag_pipeline()
        
        logger.info(f"Conversation engine initialized with model: {self._model_id}")

    def _initialize_bedrock_client(self) -> ChatBedrock:
        """Configure and return the Bedrock LLM instance."""
        # Create Bedrock runtime client
        bedrock_client = boto3.client(
            service_name="bedrock-runtime",
            region_name=self._region
        )
        
        return ChatBedrock(
            client=bedrock_client,
            model_id=self._model_id,
            model_kwargs={
                "temperature": self.DEFAULT_TEMPERATURE,
                "max_tokens": 1024
            }
        )

    def _build_rag_pipeline(self):
        """Construct the retrieval-augmented generation chain."""
        prompt_template = ChatPromptTemplate.from_messages([
            ("system", ASSISTANT_SYSTEM_PROMPT),
            ("human", "{input}")
        ])
        
        retriever = self._knowledge_store.create_retriever()
        
        document_chain = create_stuff_documents_chain(
            self._llm,
            prompt_template
        )
        
        return create_retrieval_chain(retriever, document_chain)

    def generate_response(self, user_message: str) -> str:
        """
        Process a user query and generate an informed response.

        Args:
            user_message: The user's question or message.

        Returns:
            Generated response string.
        """
        logger.debug(f"Processing query: {user_message[:50]}...")
        
        try:
            result = self._chain.invoke({"input": user_message})
            response_text = result.get("answer", "")
            
            logger.debug("Response generated successfully")
            return response_text
            
        except Exception as error:
            logger.error(f"Error generating response: {error}")
            return self._generate_fallback_response()

    def _generate_fallback_response(self) -> str:
        """Return a graceful fallback message on errors."""
        return (
            "I apologize, but I'm having difficulty processing your request "
            "at the moment. Please try rephrasing your question or try again later."
        )

    def get_detailed_response(self, user_message: str) -> Dict[str, Any]:
        """
        Generate response with additional context and metadata.

        Args:
            user_message: The user's question.

        Returns:
            Dictionary containing answer and source documents.
        """
        result = self._chain.invoke({"input": user_message})
        
        return {
            "answer": result.get("answer", ""),
            "context": result.get("context", []),
            "input": user_message
        }

    @classmethod
    def list_available_models(cls) -> list:
        """Return list of available Bedrock model names."""
        return list(cls.BEDROCK_MODELS.keys())


def create_conversation_engine(
    index_name: str,
    model: str = None
) -> IntelligentResponder:
    """
    Factory function to create a fully configured conversation engine.

    Args:
        index_name: Name of the knowledge base index.
        model: Optional Bedrock model name.

    Returns:
        Ready-to-use IntelligentResponder instance.
    """
    store = KnowledgeStore(index_name)
    store.connect_to_existing()
    
    return IntelligentResponder(
        knowledge_store=store,
        model_name=model
    )
