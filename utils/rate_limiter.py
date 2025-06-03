"""
Rate Limiter Implementation
Manages API call rate limiting to prevent quota exhaustion
"""

import time
from collections import defaultdict, deque
from typing import Dict, Deque
from utils.logger import get_logger

class RateLimiter:
    """
    Token bucket rate limiter for managing API requests
    """
    
    def __init__(self, max_requests: int = 10, time_window: int = 60):
        """
        Initialize rate limiter
        
        Args:
            max_requests: Maximum number of requests allowed in time window
            time_window: Time window in seconds
        """
        self.max_requests = max_requests
        self.time_window = time_window
        self.requests: Dict[str, Deque[float]] = defaultdict(deque)
        self.logger = get_logger(__name__)
        
        self.logger.info(f"Rate limiter initialized: {max_requests} requests per {time_window}s")
    
    def check_rate_limit(self, identifier: str) -> bool:
        """
        Check if a request is within rate limits
        
        Args:
            identifier: Unique identifier (e.g., user ID, IP address)
            
        Returns:
            True if request is allowed, False if rate limited
        """
        current_time = time.time()
        user_requests = self.requests[identifier]
        
        # Remove old requests outside the time window
        while user_requests and user_requests[0] <= current_time - self.time_window:
            user_requests.popleft()
        
        # Check if user has exceeded rate limit
        if len(user_requests) >= self.max_requests:
            self.logger.debug(f"Rate limit exceeded for {identifier}")
            return False
        
        # Add current request
        user_requests.append(current_time)
        return True
    
    def get_remaining_requests(self, identifier: str) -> int:
        """
        Get number of remaining requests for an identifier
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        user_requests = self.requests[identifier]
        
        # Remove old requests outside the time window
        while user_requests and user_requests[0] <= current_time - self.time_window:
            user_requests.popleft()
        
        return max(0, self.max_requests - len(user_requests))
    
    def get_reset_time(self, identifier: str) -> float:
        """
        Get time until rate limit resets for an identifier
        
        Args:
            identifier: Unique identifier
            
        Returns:
            Seconds until rate limit resets
        """
        current_time = time.time()
        user_requests = self.requests[identifier]
        
        if not user_requests:
            return 0
        
        # Remove old requests outside the time window
        while user_requests and user_requests[0] <= current_time - self.time_window:
            user_requests.popleft()
        
        if len(user_requests) < self.max_requests:
            return 0
        
        # Time until oldest request expires
        return user_requests[0] + self.time_window - current_time
    
    def reset_user(self, identifier: str):
        """
        Reset rate limit for a specific identifier
        
        Args:
            identifier: Unique identifier to reset
        """
        if identifier in self.requests:
            del self.requests[identifier]
            self.logger.info(f"Rate limit reset for {identifier}")
    
    def get_stats(self) -> Dict:
        """
        Get rate limiter statistics
        
        Returns:
            Dictionary containing statistics
        """
        current_time = time.time()
        total_users = len(self.requests)
        active_users = 0
        total_recent_requests = 0
        
        for identifier, user_requests in self.requests.items():
            # Count requests within time window
            recent_requests = sum(1 for req_time in user_requests 
                                if req_time > current_time - self.time_window)
            if recent_requests > 0:
                active_users += 1
                total_recent_requests += recent_requests
        
        return {
            'total_users_tracked': total_users,
            'active_users': active_users,
            'total_recent_requests': total_recent_requests,
            'max_requests_per_window': self.max_requests,
            'time_window': self.time_window
        }
    
    def cleanup_old_entries(self):
        """
        Clean up old entries to prevent memory leaks
        Should be called periodically
        """
        current_time = time.time()
        cleanup_threshold = current_time - (self.time_window * 2)  # Keep data for 2x time window
        
        identifiers_to_remove = []
        
        for identifier, user_requests in self.requests.items():
            # Remove old requests
            while user_requests and user_requests[0] <= cleanup_threshold:
                user_requests.popleft()
            
            # If no recent requests, remove the identifier
            if not user_requests:
                identifiers_to_remove.append(identifier)
        
        for identifier in identifiers_to_remove:
            del self.requests[identifier]
        
        if identifiers_to_remove:
            self.logger.debug(f"Cleaned up {len(identifiers_to_remove)} inactive rate limit entries")

class GlobalRateLimiter:
    """
    Global rate limiter for overall API usage management
    """
    
    def __init__(self, max_requests_per_minute: int = 60):
        """
        Initialize global rate limiter
        
        Args:
            max_requests_per_minute: Maximum requests per minute globally
        """
        self.max_requests_per_minute = max_requests_per_minute
        self.requests: Deque[float] = deque()
        self.logger = get_logger(__name__)
        
        self.logger.info(f"Global rate limiter initialized: {max_requests_per_minute} requests per minute")
    
    def check_global_rate_limit(self) -> bool:
        """
        Check if a request is within global rate limits
        
        Returns:
            True if request is allowed, False if rate limited
        """
        current_time = time.time()
        
        # Remove requests older than 1 minute
        while self.requests and self.requests[0] <= current_time - 60:
            self.requests.popleft()
        
        # Check if global rate limit exceeded
        if len(self.requests) >= self.max_requests_per_minute:
            self.logger.warning("Global rate limit exceeded")
            return False
        
        # Add current request
        self.requests.append(current_time)
        return True
    
    def get_global_remaining_requests(self) -> int:
        """
        Get number of remaining global requests
        
        Returns:
            Number of remaining requests
        """
        current_time = time.time()
        
        # Remove requests older than 1 minute
        while self.requests and self.requests[0] <= current_time - 60:
            self.requests.popleft()
        
        return max(0, self.max_requests_per_minute - len(self.requests))
