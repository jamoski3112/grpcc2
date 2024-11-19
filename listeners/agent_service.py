import grpc

from concurrent import futures

from typing import Dict

import uuid

from datetime import datetime

import os
from pathlib import Path



# These will be generated after running the protoc command

from protos import agent_pb2

from protos import agent_pb2_grpc



class AgentServicer(agent_pb2_grpc.AgentServiceServicer):

    def __init__(self):

        self.agents: Dict[str, agent_pb2.SystemInfo] = {}

        self.tasks: Dict[str, Dict[str, agent_pb2.Task]] = {}  # agent_id -> {task_id -> task}

        self.results: Dict[str, agent_pb2.TaskResult] = {}

        self.downloads_dir = Path("downloads")

        self.downloads_dir.mkdir(exist_ok=True)

        self.current_files = {}  # file_id -> file_handle



    def Register(self, request: agent_pb2.SystemInfo, context) -> agent_pb2.RegisterResponse:

        print(f"\nNew agent registration from {request.hostname}")

        print(f"Agent ID: {request.agent_id}")

        print(f"OS: {request.os}")

        print(f"Architecture: {request.arch}")

        print(f"Username: {request.username}")

        self.agents[request.agent_id] = request

        return agent_pb2.RegisterResponse(

            success=True,

            message=f"Successfully registered agent {request.agent_id}"

        )



    def Checkin(self, request: agent_pb2.CheckinRequest, context) -> agent_pb2.CheckinResponse:

        agent_id = request.agent_id

        has_tasks = agent_id in self.tasks and len(self.tasks[agent_id]) > 0

        return agent_pb2.CheckinResponse(has_tasks=has_tasks)



    def GetTasks(self, request: agent_pb2.TaskRequest, context) -> agent_pb2.TaskResponse:

        agent_id = request.agent_id

        if agent_id not in self.tasks:

            return agent_pb2.TaskResponse(tasks=[])

        

        tasks = list(self.tasks[agent_id].values())

        # Clear tasks after sending

        self.tasks[agent_id] = {}

        return agent_pb2.TaskResponse(tasks=tasks)



    def SendResult(self, request: agent_pb2.TaskResult, context) -> agent_pb2.ResultResponse:

        self.results[request.task_id] = request

        print(f"\nReceived result from agent {request.agent_id}")

        print(f"Task ID: {request.task_id}")

        print(f"Status: {request.status}")

        print("Output:")

        print("-" * 50)

        print(request.output)

        print("-" * 50)

        if request.error:

            print(f"Error: {request.error}")

        

        return agent_pb2.ResultResponse(

            success=True,

            message="Result received successfully"

        )



    def add_task(self, agent_id: str, command: str) -> str:

        """Helper method to add a new task for an agent"""

        if agent_id not in self.tasks:

            self.tasks[agent_id] = {}

            

        task_id = str(uuid.uuid4())

        task = agent_pb2.Task(

            id=task_id,

            command=command,

            created=datetime.now().isoformat()

        )

        

        self.tasks[agent_id][task_id] = task

        print(f"\nAdded task {task_id} for agent {agent_id}")

        print(f"Command: {command}")

        return task_id



    def SendFile(self, request_iterator, context):

        file_handle = None

        file_id = None

        file_path = None

        

        try:

            for chunk in request_iterator:

                if file_handle is None:

                    # First chunk, create the file

                    file_id = chunk.file_id

                    agent_dir = self.downloads_dir / chunk.agent_id

                    agent_dir.mkdir(exist_ok=True)

                    file_path = agent_dir / chunk.file_name

                    file_handle = open(file_path, 'wb')

                    print(f"\nReceiving file: {chunk.file_name} from agent {chunk.agent_id}")

                

                if not chunk.is_last:

                    file_handle.write(chunk.content)

                

                if chunk.is_last:

                    file_handle.close()

                    print(f"File download complete: {file_path}")

                    return agent_pb2.FileResponse(

                        success=True,

                        message=f"File {chunk.file_name} received successfully"

                    )

            

        except Exception as e:

            if file_handle:

                file_handle.close()

            if file_path and file_path.exists():

                file_path.unlink()  # Delete partial file

            return agent_pb2.FileResponse(

                success=False,

                message=f"File transfer failed: {str(e)}"

            )
