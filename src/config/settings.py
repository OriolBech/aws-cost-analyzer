from typing import Dict, List

class Settings:
    COST_PROFILES: Dict[str, List[str]] = {
        "storage": [
            "Amazon S3",
            "Amazon Glacier",
            "Amazon EFS",
            "AWS Backup",
            "AWS Elastic Container Registry"
        ],
        "compute": [
            "Amazon EC2",
            "AWS Lambda",
            "AWS Fargate",
            "Amazon Lightsail",
        ],
        "databases": [
            "Amazon Relational Database Service",
            "Amazon DynamoDB",
            "Amazon Aurora",
            "Amazon ElastiCache",
        ],
        "backups": [
            "AWS Backup",
            "Amazon S3 Glacier",
            "Amazon RDS Snapshots",
            "Amazon EBS Snapshots",
        ],
        "all": []  # Empty means no filter
    }

    @classmethod
    def get_services_for_profile(cls, profile: str) -> List[str]:
        return cls.COST_PROFILES.get(profile, []) 