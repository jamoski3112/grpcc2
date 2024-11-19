from typing import Optional
from .base_listener import BaseListener
from .grpc_listener import GRPCListener

class ListenerManager:
    def __init__(self):
        self.current_listener: Optional[BaseListener] = None
        self.listener_types = {
            'grpc': GRPCListener
        }
    
    def configure_listener(self, listener_type: str):
        if listener_type not in self.listener_types:
            print(f"Unsupported listener type: {listener_type}")
            return
            
        # Create new listener instance
        listener_class = self.listener_types[listener_type]
        self.current_listener = listener_class()
        
        # Configure the listener
        self.current_listener.configure()
    
    def start_current_listener(self):
        if self.current_listener is None:
            print("No listener configured. Use 'uselistener' command first.")
            return
            
        self.current_listener.start()
    
    def stop_current_listener(self):
        if self.current_listener is None:
            print("No listener is running.")
            return
            
        self.current_listener.stop() 