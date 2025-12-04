"""
HealthAI Assistant - Application Entry Point
--------------------------------------------
Run this script to start the development server.
"""

import sys
import os

# Add project root to path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from web.server import create_application, run_development_server
from config.settings import get_settings


def main():
    """Application entry point."""
    settings = get_settings()
    
    print(f"""
    ╔══════════════════════════════════════════════════════╗
    ║         HealthAI Assistant v{settings.version}                ║
    ╠══════════════════════════════════════════════════════╣
    ║  Starting development server...                      ║
    ║  Access the application at:                          ║
    ║  http://{settings.server.host}:{settings.server.port}                            ║
    ╚══════════════════════════════════════════════════════╝
    """)
    
    # Validate configuration
    validation = settings.validate_all()
    
    if not all(validation.values()):
        print("\n⚠️  Configuration Warning:")
        for key, valid in validation.items():
            status = "✓" if valid else "✗"
            print(f"    {status} {key.upper()}")
        print("\n    Please check your .env file.\n")
    
    run_development_server()


if __name__ == "__main__":
    main()
