# Base image
FROM python:3.11

# Set the working directory inside the container
WORKDIR /app

# Copy all files into the container
COPY . /app

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Set PYTHONPATH so imports work
ENV PYTHONPATH="/app/src"

# Define entrypoint
ENTRYPOINT ["python", "src/cli.py"]