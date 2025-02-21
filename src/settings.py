# settings.py - Defines cost analysis profiles

COST_PROFILES = {
    "storage": [
        "Amazon S3",
        "Amazon Glacier",
        "Amazon EFS",
        "AWS Backup",
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
    "all": []  # Empty means no filter, fetch all services
}