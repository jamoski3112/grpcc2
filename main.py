import os
import sys
from pathlib import Path

# Add the project root to Python path
sys.path.append(str(Path(__file__).parent))

from prompt_toolkit import PromptSession
from prompt_toolkit.completion import WordCompleter
from listeners.listener_manager import ListenerManager

def main():
    session = PromptSession()
    listener_manager = ListenerManager()
    
    # Create command completer
    commands = ['uselistener', 'start', 'stop', 'help', 'exit', 'task']
    command_completer = WordCompleter(commands)
    
    while True:
        try:
            # Get input with auto-completion
            user_input = session.prompt('terminal> ', completer=command_completer)
            
            if user_input.strip() == '':
                continue
                
            if user_input.strip() == 'exit':
                break
                
            # Handle uselistener command
            if user_input.startswith('uselistener'):
                parts = user_input.split()
                if len(parts) > 1:
                    listener_type = parts[1]
                    listener_manager.configure_listener(listener_type)
                else:
                    print("Usage: uselistener <type>")
                    print("Available types: grpc")
            
            # Handle task command
            elif user_input.startswith('task'):
                parts = user_input.split(maxsplit=2)
                if len(parts) == 3:
                    agent_id = parts[1]
                    command = parts[2]
                    if listener_manager.current_listener:
                        task_id = listener_manager.current_listener.add_task(agent_id, command)
                        print(f"Task {task_id} added for agent {agent_id}")
                    else:
                        print("No listener is running")
                else:
                    print("Usage: task <agent_id> <command>")
                    
            # Handle start command
            elif user_input.strip() == 'start':
                listener_manager.start_current_listener()
                
            # Handle stop command
            elif user_input.strip() == 'stop':
                listener_manager.stop_current_listener()
                
            elif user_input.strip() == 'help':
                print_help()
                
        except KeyboardInterrupt:
            continue
        except EOFError:
            break

def print_help():
    print("\nAvailable commands:")
    print("  uselistener <type>  - Configure a new listener (grpc)")
    print("  start              - Start the configured listener")
    print("  stop               - Stop the current listener")
    print("  task <agent_id> <command> - Send a command to an agent")
    print("  help               - Show this help message")
    print("  exit               - Exit the application\n")

if __name__ == '__main__':
    main() 