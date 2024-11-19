from prompt_toolkit import prompt

from prompt_toolkit.validation import Validator, ValidationError

from .base_listener import BaseListener

import grpc

from concurrent import futures

import threading

from .agent_service import AgentServicer

from protos import agent_pb2_grpc

from pathlib import Path



class PortValidator(Validator):

    def validate(self, document):

        text = document.text

        if not text.isdigit() or not (1 <= int(text) <= 65535):

            raise ValidationError(message='Please enter a valid port number (1-65535)')



class GRPCListener(BaseListener):

    def __init__(self):

        super().__init__()

        self.servicer = AgentServicer()



    def configure(self):

        print("\nConfiguring gRPC Listener:")

        self.config['host'] = '0.0.0.0'

        self.config['port'] = prompt('Enter port (default: 443): ') or '443'

        self.config['cert_path'] = prompt('Enter path to SSL certificate: ')

        self.config['key_path'] = prompt('Enter path to SSL private key: ')

        self.config['server_name'] = prompt('Enter server name (domain): ')

        print(f"\nConfiguration complete: {self.config}")

    

    def start(self):

        if self.is_running:

            print("Listener is already running")

            return

            

        try:

            # Load SSL credentials

            with open(self.config['key_path'], 'rb') as f:

                private_key = f.read()

            with open(self.config['cert_path'], 'rb') as f:

                certificate_chain = f.read()

                

            server_credentials = grpc.ssl_server_credentials(

                [(private_key, certificate_chain)],

                root_certificates=certificate_chain,

                require_client_auth=False

            )

                

            print(f"Starting gRPC listener on {self.config['host']}:{self.config['port']} (SSL enabled)")

            self.server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

            

            # Add the agent service

            agent_pb2_grpc.add_AgentServiceServicer_to_server(self.servicer, self.server)

            

            # Use SSL port

            port = self.server.add_secure_port(

                f"{self.config['host']}:{self.config['port']}", 

                server_credentials

            )

            

            if port == 0:

                raise Exception(f"Failed to bind to port {self.config['port']}. Make sure you have the necessary permissions.")

            

            self.server.start()

            self.is_running = True

            

            print(f"Server name: {self.config['server_name']}")

            print(f"Certificate path: {self.config['cert_path']}")

            

            # Start in a separate thread to keep the terminal responsive

            self.thread = threading.Thread(target=self.server.wait_for_termination)

            self.thread.daemon = True

            self.thread.start()

            

            print("gRPC listener started successfully with SSL")

            

        except Exception as e:

            print(f"Failed to start listener: {str(e)}")

            self.is_running = False

    

    def stop(self):

        if not self.is_running:

            print("Listener is not running")

            return

            

        print("Stopping gRPC listener...")

        self.server.stop(0)

        self.is_running = False

        print("gRPC listener stopped successfully")



    def add_task(self, agent_id: str, command: str) -> str:

        """Add a task for an agent"""

        return self.servicer.add_task(agent_id, command)
