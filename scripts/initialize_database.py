"""
Knowledge Base Initialization Script - AWS Native
--------------------------------------------------
Processes documents and creates the OpenSearch Serverless index.
Run this once before starting the application.
"""

import sys
import os

# Add project root to path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from dotenv import load_dotenv

from core.document_processor import load_knowledge_base
from core.text_chunker import create_text_segments
from services.vector_database import initialize_knowledge_base
from config.settings import get_settings


def main():
    """Initialize the knowledge base with documents in AWS OpenSearch."""
    load_dotenv()
    settings = get_settings()
    
    print("""
    ╔══════════════════════════════════════════════════════╗
    ║  HealthAI Knowledge Base Initialization (AWS)        ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # Validate AWS configuration
    if not settings.aws.validate():
        print("❌ Error: OPENSEARCH_ENDPOINT not found in environment.")
        print("   Please configure your .env file with AWS settings.")
        print("\n   Required:")
        print("   - OPENSEARCH_ENDPOINT")
        print("   - AWS_REGION")
        print("\n   Ensure your AWS credentials are configured via:")
        print("   - IAM role (on EC2)")
        print("   - aws configure (local development)")
        sys.exit(1)
    
    knowledge_path = settings.knowledge_base_path
    index_name = settings.database.index_name
    
    print(f"☁️  AWS Region: {settings.aws.region}")
    print(f"🔍 OpenSearch Endpoint: {settings.aws.opensearch_endpoint[:50]}...")
    print(f"📁 Loading documents from: {knowledge_path}")
    
    # Load and process documents
    documents = load_knowledge_base(knowledge_path)
    print(f"   ✓ Loaded {len(documents)} document pages")
    
    # Create text chunks
    print(f"\n📄 Segmenting documents...")
    chunks = create_text_segments(documents, segment_size=500, overlap=50)
    print(f"   ✓ Created {len(chunks)} text segments")
    
    # Initialize vector store in OpenSearch
    print(f"\n🔄 Initializing OpenSearch index: {index_name}")
    print("   This may take several minutes...")
    
    store = initialize_knowledge_base(index_name, chunks)
    
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║  ✅ Knowledge base initialization complete!          ║
    ╠══════════════════════════════════════════════════════╣
    ║  Index Name : {index_name:<38} ║
    ║  Documents  : {len(documents):<38} ║
    ║  Chunks     : {len(chunks):<38} ║
    ║  Storage    : AWS OpenSearch Serverless              ║
    ╚══════════════════════════════════════════════════════╝
    
    You can now run the application with: python run.py
    """)


if __name__ == "__main__":
    main()
