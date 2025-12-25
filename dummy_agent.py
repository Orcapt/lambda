"""
Orca Dummy Agent - Comprehensive Example
========================================

This dummy agent demonstrates ALL features available in orca-pip:
- Core: OrcaHandler, Session management
- Streaming: Real-time content streaming
- Loading indicators: Multiple loading states (thinking, searching, coding, analyzing, generating, general)
- Buttons: Link and action buttons
- Media: Image, Video (including YouTube), Location, Card List, Audio
- Variables: Environment variable management
- Memory: User memory system
- Storage: File storage operations
- Patterns: Builder, Middleware, Context Managers
- Decorators: retry, log_execution, measure_time, handle_errors
- Exceptions: Comprehensive error handling
- Logging: Structured logging
- Type guards: Runtime type validation
- Usage tracking: Token and cost tracking
- Tracing: Debug tracing (send, begin, append, end)
- Lambda: AWS Lambda deployment
- Utilities: All helper functions
"""

import asyncio
import logging
import os
import time
from typing import Optional
from pathlib import Path

# Core imports
from orca import (
    OrcaHandler,
    ChatMessage,
    Variables,
    MemoryHelper,
    setup_logging,
    get_logger,
    get_variable_value,
    get_openai_api_key,
    decode_base64_file,
    create_success_response,
)

# Storage SDK
from orca import OrcaStorage

# Design Patterns
from orca import (
    OrcaBuilder,
    SessionBuilder,
    SessionContext,
    ResourceContext,
    timed_operation,
    suppress_exceptions,
    Middleware,
    LoggingMiddleware,
    ValidationMiddleware,
    TransformMiddleware,
    MiddlewareChain,
    MiddlewareManager,
)

# Decorators
from orca import (
    retry,
    log_execution,
    measure_time,
    handle_errors,
    deprecated,
)

# Exceptions
from orca import (
    OrcaException,
    ConfigurationError,
    ValidationError,
    CommunicationError,
    StreamError,
    APIError,
    BufferError,
)

# Config
from orca.config import LoadingKind, ButtonColor, TokenType

# Lambda adapter
from orca import LambdaAdapter, create_lambda_handler

# Setup logging
# In Lambda, /var/task is read-only, so use /tmp for log files
is_lambda = os.environ.get("AWS_LAMBDA_FUNCTION_NAME") is not None
log_file_path = "/tmp/dummy_agent.log" if is_lambda else "dummy_agent.log"

setup_logging(
    level=logging.INFO,
    log_file=log_file_path,
    enable_colors=not is_lambda  # Disable colors in Lambda (CloudWatch doesn't support them)
)
logger = get_logger(__name__)


# ============================================================================
# 1. DECORATORS DEMONSTRATION
# ============================================================================

@retry(max_attempts=3, delay=1.0, backoff=2.0)
@log_execution(level=logging.INFO, include_args=True, include_result=True)
@measure_time
def external_api_call(url: str) -> dict:
    """Simulate external API call with retry and logging."""
    logger.info(f"Calling API: {url}")
    # Simulate API call
    return {"status": "success", "data": "API response"}


@handle_errors(default_return=None, exception_class=ValueError, log_level=logging.ERROR)
def risky_operation(value: int) -> Optional[int]:
    """Operation that might fail."""
    if value < 0:
        raise ValueError("Value must be positive")
    return value * 2


@deprecated("Use new_function() instead")
def old_function():
    """Deprecated function."""
    return "old result"


# ============================================================================
# 2. MIDDLEWARE DEMONSTRATION
# ============================================================================

class CustomAuthMiddleware(Middleware):
    """Custom authentication middleware."""
    
    def process_request(self, data):
        """Process authentication info (log only, don't modify Pydantic model)."""
        logger.info("Authenticating request...")
        if hasattr(data, 'message'):
            # Log auth context (can't modify Pydantic model directly)
            auth_context = {"authenticated": True, "user_id": "dummy-user"}
            logger.info(f"Auth context: {auth_context}")
        return data
    
    def process_response(self, response, request_data):
        """Add auth headers to response (if response is dict)."""
        if isinstance(response, dict):
            response['auth_checked'] = True
        return response


# ============================================================================
# 3. MAIN AGENT CLASS
# ============================================================================

class DummyAgent:
    """
    Comprehensive dummy agent demonstrating all orca-pip features.
    """
    
    def __init__(self, dev_mode: bool = True, stream_delay: float = 0.3):
        """
        Initialize agent with all features.
        
        Args:
            dev_mode: Enable dev mode
            stream_delay: Delay between streams in seconds (default: 0.3)
        """
        # Use Builder pattern
        self.handler = (
            OrcaBuilder()
            .with_dev_mode(dev_mode)
            .build()
        )
        
        # Setup middleware chain
        self.middleware_manager = MiddlewareManager()
        self.middleware_manager.use(LoggingMiddleware())
        self.middleware_manager.use(CustomAuthMiddleware())
        
        # Stream delay configuration
        self.stream_delay = stream_delay
        
        # Initialize storage (if credentials available)
        self.storage = None
        try:
            import os
            if os.getenv('ORCA_WORKSPACE') and os.getenv('ORCA_TOKEN'):
                self.storage = OrcaStorage(
                    workspace=os.getenv('ORCA_WORKSPACE'),
                    token=os.getenv('ORCA_TOKEN'),
                    base_url=os.getenv('STORAGE_URL', 'http://localhost:8000/api/v1/storage'),
                    mode='dev' if dev_mode else 'prod'
                )
        except Exception as e:
            logger.warning(f"Storage not available: {e}")
        
        logger.info("DummyAgent initialized with all features")
    
    def _stream_with_delay(self, session, content: str, delay: float = None):
        """
        Stream content with delay.
        
        Args:
            session: Session object
            content: Content to stream
            delay: Delay in seconds (uses self.stream_delay if None)
        """
        session.stream(content)
        time.sleep(delay if delay is not None else self.stream_delay)
    
    def _add_stream_with_delay(self, builder, content: str, delay: float = None):
        """
        Add stream to SessionBuilder with delay.
        
        Args:
            builder: SessionBuilder object
            content: Content to stream
            delay: Delay in seconds (uses self.stream_delay if None)
        """
        builder.add_stream(content)
        time.sleep(delay if delay is not None else self.stream_delay)
        return builder
    
    def _show_loading_with_delay(self, session, kind: str, duration: float = 1.5):
        """
        Show loading indicator with delay for frontend visibility.
        
        Args:
            session: Session object
            kind: Loading kind (thinking, searching, coding, etc.)
            duration: How long to show loading (default: 1.5 seconds)
        """
        session.loading.start(kind)
        time.sleep(duration)  # Give frontend time to show loading
        session.loading.end(kind)
        time.sleep(self.stream_delay)  # Small delay after hiding
    
    def _close_session_with_delay(self, session, final_delay: float = 0.5):
        """
        Close session with a delay to ensure all chunks are sent incrementally.
        
        Args:
            session: Session object to close
            final_delay: Delay before closing to ensure all chunks are sent (default: 0.5 seconds)
        
        Returns:
            Full response content as string
        """
        time.sleep(final_delay)  # Ensure all previous chunks are sent incrementally
        return session.close()
    
    # ========================================================================
    # 4. BASIC SESSION MANAGEMENT
    # ========================================================================
    
    def basic_session_example(self, data: ChatMessage):
        """Basic session management example with proper delays."""
        logger.info("=== Basic Session Example ===")
        
        # Start session
        session = self.handler.begin(data)
        
        # Show loading first
        self._show_loading_with_delay(session, LoadingKind.THINKING.value, duration=1.0)
        
        # Stream content with delay
        self._stream_with_delay(session, "Hello! ")
        self._stream_with_delay(session, "This is a basic example.")
        
        # Close session with delay to ensure incremental sending
        return self._close_session_with_delay(session)
    
    # ========================================================================
    # 5. LOADING INDICATORS
    # ========================================================================
    
    def loading_indicators_example(self, data: ChatMessage):
        """Demonstrate all loading indicators with proper delays."""
        logger.info("=== Loading Indicators Example ===")
        
        session = self.handler.begin(data)
        
        # Different loading states with delays for frontend visibility
        self._show_loading_with_delay(session, LoadingKind.THINKING.value, duration=1.5)
        self._stream_with_delay(session, "🤔 Thinking completed!\n\n")
        
        self._show_loading_with_delay(session, LoadingKind.ANALYZING.value, duration=1.5)
        self._stream_with_delay(session, "📊 Analysis completed!\n\n")
        
        self._show_loading_with_delay(session, LoadingKind.GENERATING.value, duration=1.5)
        self._stream_with_delay(session, "✨ Generation completed!\n\n")
        
        self._show_loading_with_delay(session, LoadingKind.GENERAL.value, duration=1.5)
        self._stream_with_delay(session, "⏳ Processing completed!\n\n")
        
        # Test other loading kinds
        self._show_loading_with_delay(session, LoadingKind.SEARCHING.value, duration=1.5)
        self._stream_with_delay(session, "🔍 Search completed!\n\n")
        
        self._show_loading_with_delay(session, LoadingKind.CODING.value, duration=1.5)
        self._stream_with_delay(session, "💻 Code generation completed!\n")
        
        return self._close_session_with_delay(session)
    
    # ========================================================================
    # 6. BUTTONS
    # ========================================================================
    
    def buttons_example(self, data: ChatMessage):
        """Demonstrate button features with proper delays."""
        logger.info("=== Buttons Example ===")
        
        session = self.handler.begin(data)
        self._stream_with_delay(session, "Here are some options:\n\n")
        time.sleep(self.stream_delay)
        
        # Link buttons
        session.button.link(
            "Visit Documentation",
            "https://docs.example.com",
            color=ButtonColor.PRIMARY.value
        )
        time.sleep(self.stream_delay)
        
        session.button.link(
            "GitHub Repository",
            "https://github.com/example/repo",
            color=ButtonColor.SUCCESS.value
        )
        time.sleep(self.stream_delay)
        
        # Action buttons
        session.button.action(
            "Regenerate Response",
            "regenerate",
            color=ButtonColor.SECONDARY.value
        )
        time.sleep(self.stream_delay)
        
        session.button.action(
            "Save to Favorites",
            "save_favorite",
            color=ButtonColor.INFO.value
        )
        time.sleep(self.stream_delay)
        
        # Button groups
        session.button.begin(default_color=ButtonColor.PRIMARY.value)
        session.button.add_link("Option 1", "https://option1.com")
        time.sleep(self.stream_delay)
        session.button.add_link("Option 2", "https://option2.com")
        time.sleep(self.stream_delay)
        session.button.add_action("Action 1", "action1")
        time.sleep(self.stream_delay)
        session.button.end()
        
        return self._close_session_with_delay(session)
    
    # ========================================================================
    # 6.5. MEDIA OPERATIONS (Image, Video, Location, Card, Audio)
    # ========================================================================
    
    def media_operations_example(self, data: ChatMessage):
        """Demonstrate all media operations: image, video, location, card, audio."""
        logger.info("=== Media Operations Example ===")
        
        session = self.handler.begin(data)
        
        # Image operations with loading
        self._stream_with_delay(session, "=== Image Operations ===\n")
        self._show_loading_with_delay(session, LoadingKind.IMAGE.value, duration=1.2)
        session.image.send("https://via.placeholder.com/400x300.png?text=Orca+Test+Image")
        time.sleep(self.stream_delay)
        self._stream_with_delay(session, "✓ Image sent\n\n")
        
        # Video operations with loading
        self._stream_with_delay(session, "=== Video Operations ===\n")
        self._show_loading_with_delay(session, LoadingKind.VIDEO.value, duration=1.2)
        session.video.send("https://example.com/video.mp4")
        time.sleep(self.stream_delay)
        self._stream_with_delay(session, "✓ Video URL sent\n")
        
        self._show_loading_with_delay(session, LoadingKind.VIDEO.value, duration=1.2)
        session.video.youtube("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
        time.sleep(self.stream_delay)
        self._stream_with_delay(session, "✓ YouTube video sent\n\n")
        
        # Location operations with loading
        self._stream_with_delay(session, "=== Location Operations ===\n")
        self._show_loading_with_delay(session, LoadingKind.MAP.value, duration=1.2)
        session.location.send("35.6892, 51.3890")
        time.sleep(self.stream_delay)
        self._stream_with_delay(session, "✓ Location sent (string)\n")
        
        self._show_loading_with_delay(session, LoadingKind.MAP.value, duration=1.2)
        session.location.send_coordinates(40.7128, -74.0060)
        time.sleep(self.stream_delay)
        self._stream_with_delay(session, "✓ Location sent (coordinates)\n\n")
        
        # Card list operations with loading
        self._stream_with_delay(session, "=== Card List Operations ===\n")
        cards = [
            {
                "photo": "https://via.placeholder.com/300x200.png?text=Card+1",
                "header": "Card Title 1",
                "subheader": "Card description 1",
                "text": "Additional content for card 1"
            },
            {
                "photo": "https://via.placeholder.com/300x200.png?text=Card+2",
                "header": "Card Title 2",
                "subheader": "Card description 2",
                "text": "Additional content for card 2"
            }
        ]
        self._show_loading_with_delay(session, LoadingKind.CARD.value, duration=1.2)
        session.card.send(cards)
        time.sleep(self.stream_delay)
        self._stream_with_delay(session, f"✓ {len(cards)} cards sent\n\n")
        
        # Audio operations
        self._stream_with_delay(session, "=== Audio Operations ===\n")
        tracks = [
            {
                "label": "Track 1",
                "url": "https://example.com/audio1.mp3",
                "type": "audio/mp3"
            },
            {
                "label": "Track 2",
                "url": "https://example.com/audio2.mp3",
                "type": "audio/mp3"
            }
        ]
        session.audio.send(tracks)
        time.sleep(self.stream_delay)
        self._stream_with_delay(session, f"✓ {len(tracks)} audio tracks sent\n")
        
        return self._close_session_with_delay(session)
    
    # ========================================================================
    # 7. VARIABLES AND MEMORY
    # ========================================================================
    
    def variables_memory_example(self, data: ChatMessage):
        """Demonstrate Variables and MemoryHelper."""
        logger.info("=== Variables and Memory Example ===")
        
        session = self.handler.begin(data)
        
        # Variables helper
        vars = Variables(data.variables) if hasattr(data, 'variables') else Variables([])
        
        self._stream_with_delay(session, "=== Variables ===\n")
        if vars.has("OPENAI_API_KEY"):
            self._stream_with_delay(session, "✓ OpenAI API Key found\n")
            # Don't log the actual key
            self._stream_with_delay(session, f"  Key length: {len(vars.get('OPENAI_API_KEY') or '')}\n")
        else:
            self._stream_with_delay(session, "✗ OpenAI API Key not found\n")
        
        # List all variables
        all_vars = vars.list_names()
        self._stream_with_delay(session, f"Total variables: {len(all_vars)}\n")
        for var_name in all_vars[:5]:  # Show first 5
            self._stream_with_delay(session, f"  - {var_name}\n")
        
        # Memory helper
        self._stream_with_delay(session, "\n=== Memory ===\n")
        memory = MemoryHelper(data.memory) if hasattr(data, 'memory') else MemoryHelper({})
        
        if memory.is_empty():
            self._stream_with_delay(session, "No user memory available\n")
        else:
            name = memory.get_name()
            if name:
                self._stream_with_delay(session, f"User name: {name}\n")
            
            goals = memory.get_goals()
            if goals:
                self._stream_with_delay(session, f"User goals: {', '.join(goals[:3])}\n")
            
            location = memory.get_location()
            if location:
                self._stream_with_delay(session, f"Location: {location}\n")
            
            interests = memory.get_interests()
            if interests:
                self._stream_with_delay(session, f"Interests: {', '.join(interests[:3])}\n")
        
        return self._close_session_with_delay(session)
    
    # ========================================================================
    # 8. USAGE TRACKING AND TRACING
    # ========================================================================
    
    def usage_tracking_example(self, data: ChatMessage):
        """Demonstrate usage tracking and tracing with proper delays."""
        logger.info("=== Usage Tracking and Tracing Example ===")
        
        session = self.handler.begin(data)
        
        # Usage tracking
        self._stream_with_delay(session, "Tracking token usage...\n\n")
        time.sleep(self.stream_delay)
        
        session.usage.track(
            tokens=1500,
            token_type=TokenType.PROMPT.value,
            cost="0.03",
            label="Input tokens"
        )
        time.sleep(self.stream_delay)
        
        session.usage.track(
            tokens=2000,
            token_type=TokenType.COMPLETION.value,
            cost="0.06",
            label="Output tokens"
        )
        time.sleep(self.stream_delay)
        
        # Tracing
        self._stream_with_delay(session, "Tracing operations...\n\n")
        time.sleep(self.stream_delay)
        
        session.tracing.send("Starting processing", visibility="all")
        time.sleep(self.stream_delay * 2)
        session.tracing.send("Step 1: Parsing input", visibility="dev")
        time.sleep(self.stream_delay * 2)
        session.tracing.send("Step 2: Validating data", visibility="dev")
        time.sleep(self.stream_delay * 2)
        session.tracing.send("Step 3: Generating response", visibility="all")
        time.sleep(self.stream_delay * 2)
        session.tracing.send("Processing complete", visibility="all")
        time.sleep(self.stream_delay)
        
        self._stream_with_delay(session, "✓ Usage and tracing completed\n")
        
        return self._close_session_with_delay(session)
    
    # ========================================================================
    # 9. STORAGE SDK
    # ========================================================================
    
    def storage_example(self, data: ChatMessage):
        """Demonstrate Storage SDK features."""
        logger.info("=== Storage SDK Example ===")
        
        session = self.handler.begin(data)
        
        if not self.storage:
            self._stream_with_delay(session, "Storage SDK not configured (missing credentials)\n")
            return self._close_session_with_delay(session)
        
        try:
            self._stream_with_delay(session, "=== Storage Operations ===\n\n")
            
            # List buckets
            self._stream_with_delay(session, "Listing buckets...\n")
            try:
                buckets = self.storage.list_buckets()
                self._stream_with_delay(session, f"Found {len(buckets)} bucket(s)\n")
                for bucket in buckets[:3]:  # Show first 3
                    self._stream_with_delay(session, f"  - {bucket.get('name', 'N/A')}\n")
            except Exception as e:
                self._stream_with_delay(session, f"Error listing buckets: {str(e)}\n")
            
            # Upload example (if bucket exists)
            self._stream_with_delay(session, "\nUpload example:\n")
            try:
                content = b"Hello from Dummy Agent!"
                file_info = self.storage.upload_buffer(
                    bucket='demo-bucket',
                    file_name='dummy_test.txt',
                    buffer=content,
                    folder_path='dummy-agent/',
                    visibility='private',
                    generate_url=True
                )
                self._stream_with_delay(session, f"✓ Uploaded: {file_info.get('key', 'N/A')}\n")
            except Exception as e:
                self._stream_with_delay(session, f"Upload error (expected if bucket doesn't exist): {str(e)[:50]}\n")
            
        except Exception as e:
            session.error("Storage operation failed", exception=e)
        
        return self._close_session_with_delay(session)
    
    # ========================================================================
    # 10. DESIGN PATTERNS
    # ========================================================================
    
    def patterns_example(self, data: ChatMessage):
        """Demonstrate design patterns."""
        logger.info("=== Design Patterns Example ===")
        
        # SessionBuilder pattern
        builder = SessionBuilder(self.handler)
        builder.start_session(data)
        builder.show_loading(LoadingKind.THINKING.value)
        self._add_stream_with_delay(builder, "Using SessionBuilder pattern...\n")
        builder.hide_loading(LoadingKind.THINKING.value)
        builder.add_button("Learn More", "https://example.com")
        time.sleep(self.stream_delay)
        result = builder.complete()
        
        # Context manager pattern
        with SessionContext(self.handler, data) as session:
            self._stream_with_delay(session, "Using SessionContext for automatic cleanup...\n")
            session.button.link("Context Example", "https://example.com")
            # Session automatically closes on exit
        
        # Timed operation
        with timed_operation("pattern_demo"):
            # Simulate some work
            time.sleep(0.1)
        
        # Suppress exceptions
        with suppress_exceptions(ValueError):
            # This won't crash
            value = int("not a number")  # Suppressed
        
        return result
    
    # ========================================================================
    # 11. MIDDLEWARE EXAMPLE
    # ========================================================================
    
    def middleware_example(self, data: ChatMessage):
        """Demonstrate middleware pattern."""
        logger.info("=== Middleware Example ===")
        
        def process_with_middleware(d):
            """Process request through middleware."""
            session = self.handler.begin(d)
            self._stream_with_delay(session, "Request processed through middleware chain!\n")
            self._stream_with_delay(session, "✓ Authentication checked\n")
            self._stream_with_delay(session, "✓ Request logged\n")
            self._stream_with_delay(session, "✓ Validation passed\n")
            return self._close_session_with_delay(session)
        
        # Execute through middleware
        result = self.middleware_manager.execute(process_with_middleware, data)
        return result
    
    # ========================================================================
    # 12. ERROR HANDLING
    # ========================================================================
    
    def error_handling_example(self, data: ChatMessage):
        """Demonstrate comprehensive error handling."""
        logger.info("=== Error Handling Example ===")
        
        session = self.handler.begin(data)
        
        # Custom exception
        try:
            raise ValidationError(
                "This is a validation error",
                error_code="VALIDATION_ERROR",
                context={"field": "message", "value": "test"}
            )
        except ValidationError as e:
            self._stream_with_delay(session, f"Caught ValidationError: {e.message}\n")
            self._stream_with_delay(session, f"Error code: {e.error_code}\n")
            error_dict = e.to_dict()
            self._stream_with_delay(session, f"Error details: {error_dict}\n")
        
        # Stream error
        try:
            raise StreamError(
                "Stream operation failed",
                error_code="STREAM_FAILED",
                context={"channel": "test-channel"}
            )
        except StreamError as e:
            session.error("Stream error occurred", exception=e)
        
        return self._close_session_with_delay(session)
    
    # ========================================================================
    # 13. COMPREHENSIVE EXAMPLE (ALL FEATURES)
    # ========================================================================
    
    @retry(max_attempts=2)
    @log_execution(level=logging.INFO, include_args=True)
    @measure_time
    def comprehensive_example(self, data: ChatMessage):
        """Comprehensive example using ALL features with proper delays and loading indicators."""
        logger.info("=== COMPREHENSIVE EXAMPLE (ALL FEATURES) ===")
        
        # Use middleware
        def process_comprehensive(d):
            # Use SessionBuilder with delays
            builder = SessionBuilder(self.handler).start_session(d)
            
            # ========== 1. Initial Thinking Loading ==========
            builder.show_loading(LoadingKind.THINKING.value)
            builder.add_stream("🚀 Starting comprehensive demo...\n\n")
            builder.hide_loading(LoadingKind.THINKING.value)
            builder.execute()
            time.sleep(self.stream_delay)
            
            # ========== 2. Variables and Memory ==========
            builder.add_stream("📦 Variables and Memory:\n")
            builder.process(lambda s: self._show_variables_memory(s, d))
            builder.execute()
            time.sleep(self.stream_delay * 2)
            
            # ========== 3. Usage Tracking with Loading ==========
            builder.show_loading(LoadingKind.GENERAL.value)
            builder.add_stream("\n📊 Usage Tracking:\n")
            builder.track_usage(tokens=1500, token_type=TokenType.PROMPT.value, cost="0.03")
            builder.track_usage(tokens=2000, token_type=TokenType.COMPLETION.value, cost="0.06")
            builder.hide_loading(LoadingKind.GENERAL.value)
            builder.execute()
            time.sleep(self.stream_delay)
            
            # ========== 4. Tracing ==========
            builder.add_stream("\n🔍 Tracing:\n")
            builder.track_trace("Operation started", "all")
            builder.execute()
            time.sleep(self.stream_delay * 2)
            builder.track_trace("Processing data", "dev")
            builder.execute()
            time.sleep(self.stream_delay * 2)
            builder.track_trace("Operation completed", "all")
            builder.execute()
            time.sleep(self.stream_delay)
            
            # ========== 5. Buttons ==========
            builder.add_stream("\n🔘 Buttons:\n")
            builder.add_button("Documentation", "https://docs.example.com")
            builder.add_button("GitHub", "https://github.com/example")
            builder.execute()
            time.sleep(self.stream_delay)
            
            # ========== 6. Media Operations with Loading Indicators ==========
            builder.add_stream("\n🖼️ Media Operations:\n")
            
            # Image with loading
            builder.show_loading(LoadingKind.IMAGE.value)
            builder.execute()
            time.sleep(0.5)  # Show loading for frontend
            builder.hide_loading(LoadingKind.IMAGE.value)
            builder.add_image("https://via.placeholder.com/400x300.png?text=Orca+Demo")
            builder.execute()
            time.sleep(self.stream_delay)
            
            # Video with loading
            builder.show_loading(LoadingKind.VIDEO.value)
            builder.execute()
            time.sleep(0.5)  # Show loading for frontend
            builder.hide_loading(LoadingKind.VIDEO.value)
            builder.add_video("https://example.com/video.mp4")
            builder.execute()
            time.sleep(self.stream_delay)
            
            # YouTube with loading
            builder.show_loading(LoadingKind.VIDEO.value)
            builder.execute()
            time.sleep(1.2)  # Show loading for frontend
            builder.hide_loading(LoadingKind.VIDEO.value)
            builder.add_youtube("https://www.youtube.com/watch?v=dQw4w9WgXcQ")
            builder.execute()
            time.sleep(self.stream_delay)
            
            # Location with loading
            builder.show_loading(LoadingKind.MAP.value)
            builder.add_stream("Loading map...")
            builder.execute()
            time.sleep(0.5)  # Show loading for frontend
            builder.hide_loading(LoadingKind.MAP.value)
            builder.add_location_coordinates(35.6892, 51.3890)
            builder.execute()
            time.sleep(self.stream_delay)
            
            # Cards with loading
            builder.show_loading(LoadingKind.CARD.value)
            builder.execute()
            time.sleep(0.5)  # Show loading for frontend
            builder.hide_loading(LoadingKind.CARD.value)
            builder.add_card_list([
                {
                    "photo": "https://via.placeholder.com/300x200.png?text=Card+1",
                    "header": "Demo Card",
                    "subheader": "Card description",
                    "text": "Additional content"
                }
            ])
            builder.execute()
            time.sleep(self.stream_delay)
            
            # Audio
            builder.add_audio([
                {
                    "label": "Demo Track",
                    "url": "https://example.com/audio.mp3",
                    "type": "audio/mp3"
                }
            ])
            builder.execute()
            time.sleep(self.stream_delay)
            
            # ========== 7. Complete ==========
            time.sleep(0.5)  # Final delay before closing
            result = builder.close()
            
            return result
        
        # Execute through middleware
        return self.middleware_manager.execute(process_comprehensive, data)
    
    def _show_variables_memory(self, session, data: ChatMessage):
        """Helper to show variables and memory."""
        vars = Variables(data.variables) if hasattr(data, 'variables') else Variables([])
        memory = MemoryHelper(data.memory) if hasattr(data, 'memory') else MemoryHelper({})
        
        self._stream_with_delay(session, f"  Variables: {len(vars.list_names())} found\n")
        if not memory.is_empty():
            self._stream_with_delay(session, f"  Memory: User '{memory.get_name() or 'Unknown'}' has {len(memory.get_goals())} goals\n")
        else:
            self._stream_with_delay(session, "  Memory: Empty\n")
    
    # ========================================================================
    # 14. MAIN PROCESS METHOD
    # ========================================================================
    
    def process(self, data: ChatMessage, example_type: str = "comprehensive"):
        """
        Main processing method.
        
        Args:
            data: ChatMessage from Orca
            example_type: Type of example to run
                - "basic": Basic session
                - "loading": Loading indicators
                - "buttons": Buttons
                - "media": Media operations (image, video, location, card, audio)
                - "variables": Variables and memory
                - "usage": Usage tracking
                - "storage": Storage SDK
                - "patterns": Design patterns
                - "middleware": Middleware
                - "errors": Error handling
                - "comprehensive": All features (default)
        """
        examples = {
            "basic": self.basic_session_example,
            "loading": self.loading_indicators_example,
            "buttons": self.buttons_example,
            "media": self.media_operations_example,
            "variables": self.variables_memory_example,
            "usage": self.usage_tracking_example,
            "storage": self.storage_example,
            "patterns": self.patterns_example,
            "middleware": self.middleware_example,
            "errors": self.error_handling_example,
            "comprehensive": self.comprehensive_example,
        }
        
        example_func = examples.get(example_type, self.comprehensive_example)
        
        try:
            with timed_operation(f"process_{example_type}"):
                return example_func(data)
        except OrcaException as e:
            logger.error(f"Orca error: {e.to_dict()}")
            raise
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            raise


# ============================================================================
# 15. LAMBDA ADAPTER SETUP
# ============================================================================

# Determine dev mode from environment (default: False for production)
dev_mode = os.getenv("ORCA_DEV_MODE", "false").lower() == "true"

# Initialize agent
agent = DummyAgent(dev_mode=dev_mode)

# Lambda adapter
lambda_adapter = LambdaAdapter()


@lambda_adapter.message_handler
async def lambda_process_message(data: ChatMessage):
    """Lambda handler for message processing."""
    return agent.process(data, example_type="comprehensive")


@lambda_adapter.cron_handler
async def lambda_scheduled_task(event):
    """Lambda handler for scheduled tasks."""
    logger.info("Scheduled task executed")
    return {"status": "success"}


def lambda_handler(event, context):
    """AWS Lambda handler."""
    return lambda_adapter.handle(event, context)


# ============================================================================
# 16. STANDALONE USAGE
# ============================================================================

def main():
    """Standalone usage example."""
    # Create mock data
    class MockData:
        response_uuid = "dummy-uuid-123"
        thread_id = "dummy-thread-456"
        channel = "dummy-channel"
        message = "Show me all features!"
        variables = [
            {"name": "OPENAI_API_KEY", "value": "sk-test123"},
            {"name": "DATABASE_URL", "value": "postgresql://localhost/db"}
        ]
        memory = {
            "name": "Test User",
            "goals": ["Learn Python", "Build AI apps"],
            "location": "San Francisco, CA",
            "interests": ["AI", "Programming"],
            "preferences": ["Detailed explanations"],
            "past_experiences": ["Built a web scraper"]
        }
    
    data = ChatMessage(**MockData().__dict__)
    
    # Run comprehensive example
    print("\n" + "="*60)
    print("ORCA DUMMY AGENT - COMPREHENSIVE DEMO")
    print("="*60 + "\n")
    
    result = agent.process(data, example_type="comprehensive")
    print(f"\nResult: {result[:200]}...")  # Print first 200 chars


if __name__ == "__main__":
    main()

