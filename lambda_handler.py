"""
Lambda Handler - Entry Point
=============================

Simplified Lambda handler using orca-pip utilities.
Supports all FastAPI routes via Mangum + SQS/cron via LambdaAdapter.

Uses the same process_message and app from main.py for consistency.
"""

import asyncio
import logging
from typing import Any, Dict

from mangum import Mangum
from orca import ChatMessage, LambdaAdapter

from main import process_message, app

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s")

# Ensure event loop exists for Lambda (Python 3.11 quirk)
try:
    asyncio.get_event_loop()
except RuntimeError:
    asyncio.set_event_loop(asyncio.new_event_loop())

# Mangum handler for FastAPI (handles all routes: /health, /docs, /api/v1/*, etc.)
mangum_handler = Mangum(app, lifespan="off")

# LambdaAdapter for SQS and cron events
lambda_adapter = LambdaAdapter()


@lambda_adapter.message_handler
async def lambda_process_message(data: ChatMessage):
    """SQS message handler - uses same process_message from main.py."""
    return await process_message(data)


@lambda_adapter.cron_handler
async def scheduled_task(event: Dict[str, Any]):
    """Scheduled task handler (EventBridge)."""
    logger.info("Scheduled task executed")
    return {"status": "success"}


def handler(event: Dict[str, Any], context: Any) -> Dict[str, Any]:
    """
    AWS Lambda entry point.
    
    Uses LambdaAdapter.handle() for SQS/cron (auto-detects event type).
    Uses Mangum for HTTP requests (all FastAPI routes available).
    """
    # SQS or Cron - use LambdaAdapter (auto-detects and handles)
    if ("Records" in event and event.get("Records", [{}])[0].get("eventSource") == "aws:sqs") or \
       event.get("source") == "aws.events":
        return lambda_adapter.handle(event, context)
    
    # HTTP - use Mangum (all FastAPI routes: /health, /docs, /api/v1/*, etc.)
    return mangum_handler(event, context)
