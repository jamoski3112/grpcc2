from abc import ABC, abstractmethod

class BaseListener(ABC):
    def __init__(self):
        self.config = {}
        self.is_running = False
    
    @abstractmethod
    def configure(self):
        """Configure the listener with user input"""
        pass
    
    @abstractmethod
    def start(self):
        """Start the listener"""
        pass
    
    @abstractmethod
    def stop(self):
        """Stop the listener"""
        pass 