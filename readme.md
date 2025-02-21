# AWS Cost Analyzer CLI 🚀

A CLI tool to fetch and analyze AWS cost data using **Cost Explorer API**, built with **Python, Click, and Docker**.

## ✨ Features
- Retrieve AWS cost data for a specific number of days
- Filter costs by **AWS profile**
- Group costs by **AWS services**
- Export results to a CSV file
- Run **locally** or **inside Docker**

---

## 👥 Prerequisites
- Python 3.11+
- AWS CLI configured (`aws configure`)
- Docker (if running inside a container)

---

## 👅 Installation

### 1️⃣ **Clone the Repository**
```sh
git clone https://github.com/yourusername/aws-cost-analyzer.git
cd aws-cost-analyzer
```

### 2️⃣ **Set Up AWS Credentials**
Ensure AWS credentials are available via:
- `~/.aws/credentials`
- Environment variables (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`)
- AWS CLI authentication (`aws configure`)

### 3️⃣ **Install Dependencies (For Local Execution)**
```sh
python -m venv venv
source venv/bin/activate  # macOS/Linux
venv\Scripts\activate      # Windows

pip install -r requirements.txt
```

---

## 🚀 **Usage**

### **1️⃣ Running Locally**
```sh
python src/cli.py --days 30 --aws-profile default --output outputs/aws_costs.csv
```
**Options:**
| Flag | Description | Example |
|------|------------|---------|
| `--days` | Number of days to fetch cost data | `--days 7` |
| `--aws-profile` | AWS profile to use | `--aws-profile myprofile` |
| `--cost-profile` | Cost category (storage, compute, etc.) | `--cost-profile storage` |
| `--output` | Save output as CSV | `--output outputs/aws_costs.csv` |

---

### **2️⃣ Running in Docker**
---

## 📄 **License**
MIT License.

---

## 🎡 **Author**
Developed by **Oriol Bech** – feel free to reach out! 🚀