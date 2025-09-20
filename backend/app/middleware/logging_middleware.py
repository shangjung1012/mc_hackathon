import time
import uuid
from typing import Callable
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from ..core.logging import get_logger

logger = get_logger("middleware")


class LoggingMiddleware(BaseHTTPMiddleware):
    """HTTP請求日誌中間件"""
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # 生成請求ID
        request_id = str(uuid.uuid4())
        
        # 記錄請求開始
        start_time = time.time()
        
        # 獲取客戶端IP
        client_ip = request.client.host if request.client else "unknown"
        
        # 記錄請求信息
        logger.info(
            "Request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            user_agent=request.headers.get("user-agent", "unknown"),
        )
        
        # 處理請求
        try:
            response = await call_next(request)
            
            # 計算處理時間
            process_time = time.time() - start_time
            
            # 記錄響應信息
            logger.info(
                "Request completed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=round(process_time, 4),
                client_ip=client_ip,
            )
            
            # 添加請求ID到響應頭
            response.headers["X-Request-ID"] = request_id
            
            return response
            
        except Exception as e:
            # 計算處理時間
            process_time = time.time() - start_time
            
            # 記錄錯誤
            logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=round(process_time, 4),
                client_ip=client_ip,
                exc_info=True,
            )
            
            # 重新拋出異常
            raise
