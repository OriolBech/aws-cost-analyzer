import boto3
from typing import Dict, Any

class AWSClient:
    def __init__(self, profile_name: str = None):
        self.session = boto3.Session(profile_name=profile_name)
        self._clients: Dict[str, Any] = {}
        self._region = "us-east-1"

    def get_client(self, service: str, region_name: str = None) -> Any:
        """Get cached AWS client or create new one"""
        key = f"{service}:{region_name or self._region}"
        if key not in self._clients:
            self._clients[key] = self.session.client(
                service, 
                region_name=region_name or self._region
            )
        return self._clients[key] 