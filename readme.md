# AWS Cost Analyzer CLI 🚀

A CLI tool to fetch and analyze AWS cost data using **AWS Cost Explorer API**, built with **Python, Click, and Docker**.

## ✨ Features
- Retrieve AWS cost data for a specific number of days
- Filter costs by **AWS profile**
- Group costs by predefined categories (**storage**, **compute**, **databases**, **backups**, **all**)
- Automatically fetch detailed information of RDS database instances when analyzing the **databases** category, including:
  - Instance specifications (memory, vCPUs, storage)
  - Average resource utilization (CPU, memory, storage)
  - Instance sizing evaluation (optimal, low, critically low)
- Optionally export results to separate CSV files (general cost details and detailed RDS instances report)
- Run **locally** or **inside Docker**

---

## 👥 Prerequisites
- Python 3.11+
- AWS CLI configured (`aws configure`)
- Docker (optional, for containerized execution)

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
# Example with default settings (no CSV generated)
python src/cli.py --days 30

# Example specifying category and generating CSV files
python src/cli.py --days 30 --aws-profile default --category databases --output aws_cost_reports
```

**Options:**
| Flag | Description | Example |
|------|------------|---------|
| `--days` | Number of days to fetch cost data | `--days 7` |
| `--aws-profile` | AWS profile to use | `--aws-profile myprofile` |
| `--category` | Cost category (`storage`, `compute`, `databases`, `backups`, `all`) | `--category databases` |
| `--output` | (Optional) Directory to save output CSV files | `--output aws_cost_reports` |

When using the `databases` category, the CLI automatically retrieves and displays detailed information about RDS instances across all regions and saves the results in a separate CSV file if `--output` is provided.

---

## 📊 Automatic RDS Instance Sizing Evaluation

The CLI automatically evaluates your RDS instances based on the following criteria:

### 🚦 CPU Usage
- **High Usage:** Average CPU usage > **80%**
- **Optimal:** Average CPU usage between **20% - 80%**
- **Low Usage:** Average CPU usage < **20%**

### 🧠 Memory Usage (Average Free Memory)
- **Critically Low:** Free memory < **5%** of total memory
- **Low:** Free memory between **5% - 15%** of total memory
- **Optimal:** Free memory > **15%** of total memory

### 💾 Storage Usage (Average Free Storage)
- **Critically Low:** Free storage < **10%** of total storage
- **Low:** Free storage between **10% - 25%** of total storage
- **Optimal:** Free storage > **25%** of total storage

If insufficient data is available for evaluation, the CLI will clearly indicate this with **"Insufficient Data"**.

---

### **2️⃣ Running in Docker**

#### **Build the Docker Image**
```sh
docker-compose build
```

#### **Run the CLI in Docker**
```sh
docker-compose run --rm aws_cost_analyzer --days 30 --category databases --output aws_cost_reports
```

#### **Check the Output**
```sh
ls -l aws_cost_reports/
```

The CSV files will be available in the **`aws_cost_reports/`** folder.

---

## 📄 **License**
MIT License.

---

## 🎡 **Author**
Developed by **Oriol Bech** – feel free to reach out! 🚀