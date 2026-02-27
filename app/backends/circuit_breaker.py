import time 
from enum import Enum

class CircuitState(str, Enum):
    CLOSED = "closed"
    OPEN = "open"

class CircuitBreaker:
    def  __init__(
            self, 
            failure_threshold: int = 5,
            cooldown_seconds: int = 30,
    ):
        self.failure_threshold = failure_threshold
        self.cooldown_seconds = cooldown_seconds
        self.failure_count = 0
        self.last_failure_time = None
        self.state = CircuitState.CLOSED
    
    def allow_request(self)-> bool: 
        if self.state == CircuitState.CLOSED:
            return True
        
        if self.last_failure_time is None:
            return False
        
        if time.time() - self.last_failure_time > self.cooldown_seconds:
            return True
        
        return False
    
    def record_success(self):
        self.failure_count = 0
        self.state = CircuitState.CLOSED
    
    def record_failure(self):
        self.failure_count += 1
        self.last_failure_time = time.time()
        if self.failure_count >= self.failure_threshold:
            self.state = CircuitState.OPEN
            
        

