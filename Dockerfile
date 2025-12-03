# Use official Playwright Python image (includes all browser dependencies)
FROM mcr.microsoft.com/playwright/python:v1.48.0

# Create app directory
WORKDIR /app

# Copy files
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Playwright browsers already installed inside the base image
# Just start your MCP server
CMD ["python", "main.py"]
