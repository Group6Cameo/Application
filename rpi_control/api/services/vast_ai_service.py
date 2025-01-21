"""
VastAI Service Module

This module provides an interface to the VastAI API for managing cloud GPU instances.
It handles instance lifecycle operations including starting, stopping, and status checking.

Environment Variables Required:
    VAST_AI_API_KEY: API key for VastAI service authentication

Usage:
    service = VastAIService()
    result = await service.start_instance(instance_id)
"""

import os
from dotenv import load_dotenv
from vastai import VastAI
from typing import Dict, Any
import aiohttp
import asyncio
import time
from ...utils.url_store import get_backend_url

load_dotenv()


class VastAIService:
    """
    Service class for managing VastAI GPU instances.

    Attributes:
        api_key (str): VastAI API key from environment
        client (VastAI): Initialized VastAI client instance
    """

    def __init__(self):
        """Initialize VastAI service with API key from environment."""
        self.api_key = os.getenv('VAST_AI_API_KEY')
        if not self.api_key:
            raise RuntimeError(
                "VAST_AI_API_KEY environment variable is not set")
        self.client = VastAI(api_key=str(self.api_key))
        print("VAST AI SERVICE INITIALIZED")

    async def start_instance(self, instance_id: int) -> Dict[str, Any]:
        """
        Start a VastAI instance.

        Args:
            instance_id (int): ID of the instance to start

        Returns:
            Dict[str, Any]: Response containing:
                - status: "success" or "error"
                - message: Description of the result
                - details: Full response from VastAI API
        """
        try:
            print("start_instance", instance_id)
            response = self.client.start_instance(id=instance_id)
            return {
                "status": "success",
                "message": "Instance started",
                "details": response
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def stop_instance(self, instance_id: int) -> Dict[str, Any]:
        try:
            response = self.client.stop_instance(id=instance_id)
            return {
                "status": "success",
                "message": "Instance stopped",
                "details": response
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_instance_status(self, instance_id: int) -> Dict[str, Any]:
        try:
            instances = self.client.show_instances()
            instance = next(
                (i for i in instances if i['id'] == int(instance_id)),
                None)
            return {
                "status": "success",
                "running": bool(instance),
                "details": instance
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def get_instances(self) -> Dict[str, Any]:
        try:
            response = self.client.show_instances()
            return {
                "status": "success",
                "instances": response
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def _check_server_ready(self, url: str, max_retries: int = 30, delay: int = 10) -> bool:
        """
        Poll the server until it responds or max retries is reached.

        Args:
            url (str): The URL to check
            max_retries (int): Maximum number of retry attempts
            delay (int): Delay between retries in seconds

        Returns:
            bool: True if server is responding, False otherwise
        """
        # Get the backend URL for health check
        backend_url = f"{url}/"  # Add trailing slash for root endpoint

        async with aiohttp.ClientSession() as session:
            for _ in range(max_retries):
                try:
                    async with session.get(backend_url) as response:
                        if response.status == 200:
                            return True
                except aiohttp.ClientError:
                    pass
                await asyncio.sleep(delay)
            return False

    async def create_instance(self) -> Dict[str, Any]:
        try:
            response = self.client.launch_instance(
                num_gpus='1',
                gpu_name="RTX_3090",
                image="montijnb/cameosmall:v5",
                disk="40",
                min_cuda="12.4",
                onstart_cmd="uvicorn app:app --host 0.0.0.0 --port 8000"
            )
            if response.status_code == 200:
                instances = await self.get_instances()
                if instances["status"] == "success":
                    instance = instances["instances"][0]
                    port = None
                    if "ports" in instance:
                        port_mappings = instance["ports"].get("8000/tcp", [])
                        if port_mappings:
                            port = port_mappings[0].get("HostPort")

                    # Construct the URL and wait for server to be ready
                    if instance["public_ip"] and port:
                        server_url = f"http://{instance['public_ipaddr'][0]}:{port}"
                        is_ready = await self._check_server_ready(server_url)
                        if not is_ready:
                            return {"status": "error", "message": "Server failed to start within timeout period"}

                    return {
                        "status": "success",
                        "message": "Instance created and server is ready",
                        "running_instance": [inst["id"] for inst in instances["instances"]],
                        "public_ip": [inst["public_ipaddr"] for inst in instances["instances"]],
                        "port": port
                    }
            return {"status": "error", "message": "Instance creation failed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
