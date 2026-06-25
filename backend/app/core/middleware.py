import time
import uuid
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from loguru import logger


class RequestIDMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("X-Request-ID")
        if not request_id:
            request_id = str(uuid.uuid4())

        # Attach request_id to state
        request.state.request_id = request_id

        # Log incoming request
        start_time = time.time()
        with logger.contextualize(request_id=request_id):
            logger.info(f"Incoming: {request.method} {request.url.path}")
            
            try:
                response = await call_next(request)
            except Exception as e:
                logger.error(f"Request failed: {str(e)}")
                raise e
            
            process_time = (time.time() - start_time) * 1000
            logger.info(f"Completed: {request.method} {request.url.path} - Status: {response.status_code} - Processed in {process_time:.2f}ms")
            
            # Inject Request ID header
            response.headers["X-Request-ID"] = request_id
            return response
