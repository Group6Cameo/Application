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
from typing import Dict, Any, Optional

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

    async def create_instance(self) -> Dict[str, Any]:
        """
        Create a new VastAI instance.

        Returns:
            Dict[str, Any]: Response containing:
                - status: "success" or "error"
                - message: Description of the result
                - details: Full response from VastAI API
        """
        try:
            response = self.client.launch_instance(
                num_gpus="1",
                gpu_name="RTX_A4000",
                image="pytorch/pytorch:2.1.1-cuda12.1-cudnn8-runtime",
            )
            if response["status"] == "success":
                return {
                    "status": "success",
                    "message": "Instance created",
                    "details": response
                }
            return {"status": "error", "message": "Instance creation failed"}
        except Exception as e:
            return {"status": "error", "message": str(e)}
