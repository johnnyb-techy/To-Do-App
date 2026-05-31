# Use official Python image as base
FROM python:3.13.13

# Set working directory inside container
WORKDIR /app

# Copy requirements.txt into container
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy entire app into container
COPY . .

# Expose port 5000 (Flask default)
EXPOSE 5000

# Run the app when container starts
CMD ["python", "app.py"]