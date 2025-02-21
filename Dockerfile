# Use official Python image
FROM python:3.11

# Set the working directory
WORKDIR /app

# Copy project files
COPY src/ src/
COPY requirements.txt .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set PYTHONPATH so Python can find "src" as a package
ENV PYTHONPATH=/app

# Set entry point for the CLI using absolute module path
ENTRYPOINT ["python", "-m", "src.cli"]