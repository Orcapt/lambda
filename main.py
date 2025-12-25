"""
Orca Dummy Agent - API Backend
===============================

FastAPI backend with real-time streaming support.
Uses all features from orca-pip.
Only API endpoints - no UI.
"""

import asyncio
import logging
import os
from typing import Optional

from fastapi import FastAPI
from orca import (
    ChatMessage,
    OrcaHandler,
    create_orca_app,
    add_standard_endpoints,
    setup_logging,
    get_logger,
)

from dummy_agent import DummyAgent

# Setup logging
setup_logging(level=logging.INFO, enable_colors=True)
logger = get_logger(__name__)

# Determine dev mode from environment
dev_mode = os.getenv("ORCA_DEV_MODE", "false").lower() == "true"

# Initialize Orca handler
orca = OrcaHandler(dev_mode=dev_mode)

# Initialize dummy agent
agent = DummyAgent(dev_mode=dev_mode)


async def process_message(data: ChatMessage):
    """
    Main message processing function.
    Uses the dummy agent to demonstrate all orca-pip features.
    """
    logger.info(f"Processing message: {data.message[:50] if data.message else 'None'}...")
    
    # Get example type from message or use default
    example_type = "comprehensive"
    if data.message:
        message_lower = data.message.lower()
        if "basic" in message_lower:
            example_type = "basic"
        elif "loading" in message_lower:
            example_type = "loading"
        elif "button" in message_lower:
                example_type = "buttons"
        elif "media" in message_lower or "image" in message_lower or "video" in message_lower:
                example_type = "media"
        elif "variable" in message_lower or "memory" in message_lower:
                example_type = "variables"
        elif "usage" in message_lower or "tracking" in message_lower:
            example_type = "usage"
        elif "storage" in message_lower:
            example_type = "storage"
        elif "pattern" in message_lower:
            example_type = "patterns"
        elif "middleware" in message_lower:
            example_type = "middleware"
        elif "error" in message_lower:
            example_type = "errors"
        elif "all" in message_lower or "comprehensive" in message_lower:
            example_type = "comprehensive"
    
    try:
        # Wait 0.5 seconds before starting response
        await asyncio.sleep(0.5)
        
        # Process with dummy agent
        # agent.process() creates its own session and handles streaming internally
        # Run in thread to avoid blocking event loop
        result = await asyncio.to_thread(
            agent.process,
            data,
            example_type
        )
        
        logger.info(f"Message processed successfully with example_type: {example_type}")
        
    except Exception as e:
        logger.exception("Error processing message")
        # Create a session for error handling if needed
        session = orca.begin(data)
        try:
            await asyncio.to_thread(session.error, "An error occurred", exception=e)
        finally:
            await asyncio.to_thread(session.close)


# Create FastAPI app
app = create_orca_app(
    title="Orca Dummy Agent",
    version="1.0.0",
    description="Comprehensive dummy agent demonstrating all orca-pip features with real-time streaming",
)

# Add standard endpoints
add_standard_endpoints(
    app,
    conversation_manager=None,
    orca_handler=orca,
    process_message_func=process_message,
)


@app.get("/health")
async def health():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "Orca Dummy Agent",
        "version": "1.0.0",
        "dev_mode": dev_mode
    }


if __name__ == "__main__":
    import uvicorn
    
    port = int(os.getenv("PORT", "80"))
    docs_base = f"http://localhost:{port}"
    
    print("\n" + "="*70)
    print("🚀 ORCA DUMMY AGENT - API BACKEND")
    print("="*70)
    print(f"\n📖 API Documentation: {docs_base}/docs")
    print(f"🔍 Health Check: {docs_base}/api/v1/health")
    print(f"💬 Chat Endpoint: {docs_base}/api/v1/send_message")
    
    if dev_mode:
        print(f"📡 SSE Stream: {docs_base}/api/v1/stream/{{channel}}")
        print(f"📊 Poll Stream: {docs_base}/api/v1/poll/{{channel}}")
        print("\n🔧 DEV MODE ACTIVE - No Centrifugo required!")
    else:
        print("\n🟢 PRODUCTION MODE - Centrifugo/WebSocket streaming")
    
    print("\n✨ Features:")
    print("   ✅ Real-time streaming")
    print("   ✅ All orca-pip features")
    print("   ✅ API endpoints only (no UI)")
    print("="*70 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=port)
