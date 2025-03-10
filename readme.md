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

## 🏗️ Architecture

The project follows Clean Architecture and SOLID principles, organized in the following layers:

### Domain Layer (`src/domain/`)
The core business logic and rules, independent of external systems:
- `entities/`: Core business objects (Cost, DatabaseInstance)
- `value_objects/`: Immutable objects with business logic (Metrics)
- `repositories/`: Abstract interfaces for data access

### Application Layer (`src/application/`)
Contains use cases and orchestrates the domain objects:
- Business logic implementation
- Use case coordination
- No dependencies on external frameworks

### Infrastructure Layer (`src/infrastructure/`)
External systems implementation and technical details:
- `aws/`: AWS-specific implementations
  - `aws_client.py`: AWS SDK client wrapper
  - `aws_cost_repository.py`: Concrete repository implementation
- `formatters/`: Output formatting utilities
  - `csv_formatter.py`: CSV export functionality
  - `table_formatter.py`: CLI table display

### Presentation Layer (`src/presentation/`)
User interface implementation:
- `cli.py`: Command-line interface using Click
- Handles user input and output formatting

### Configuration (`src/config/`)
Application configuration and settings:
- `settings.py`: Cost profiles and other configurations

### Key Benefits of this Architecture:
- **Separation of Concerns**: Each layer has a specific responsibility
- **Dependency Rule**: Dependencies point inward
- **Testability**: Business logic can be tested without external dependencies
- **Flexibility**: Easy to swap implementations (e.g., different cloud providers)
- **Maintainability**: Clear boundaries between components

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

## 🚀 Usage

### **1️⃣ Running Locally**

```sh
# Example with default settings (no CSV generated)
python -m src.presentation.cli --days 30

# Example specifying category and generating CSV files
python -m src.presentation.cli --days 30 --aws-profile default --category databases --output aws_cost_reports
```

**Options:**
| Flag | Description | Example |
|------|------------|---------|
| `--days` | Number of days to fetch cost data | `--days 7` |
| `--aws-profile` | AWS profile to use | `--aws-profile myprofile` |
| `--category` | Cost category (`storage`, `compute`, `databases`, `backups`, `all`) | `--category databases` |
| `--output` | (Optional) Directory to save output CSV files | `--output aws_cost_reports` |

### **2️⃣ Running in Docker**

#### **Build the Docker Image**
```sh
docker-compose build
```

#### **Run the CLI in Docker**
```sh
# Basic usage
docker-compose run --rm aws_cost_analyzer

# With specific options
docker-compose run --rm aws_cost_analyzer \
  --days 30 \
  --category databases \
  --output /app/outputs
```

#### **Check the Output**
The CSV files will be available in the mounted output directory:
```sh
ls -l outputs/
```

### **3️⃣ Project Structure**
```
src/
├── application/          # Use cases and business logic
├── domain/              # Core business rules and entities
├── infrastructure/      # External implementations (AWS, formatters)
├── presentation/        # User interface (CLI)
└── config/             # Application settings
```

To add new features or modify existing ones:
1. Start with the domain layer if adding new business rules
2. Implement use cases in the application layer
3. Add infrastructure implementations if needed
4. Update the CLI in the presentation layer

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

## 📄 **License**
MIT License.

---

## 🎡 **Author**
Developed by **Oriol Bech** – feel free to reach out! 🚀