# Use an official Python runtime as a parent image
FROM python:3.8-alpine

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY requirements /app/requirements
COPY requirements.txt /app/requirements.txt

# Install any needed packages specified in requirements.txt
RUN pip install --no-cache-dir -r requirements.txt

COPY pep8speaks /app/pep8speaks
COPY server.py /app/server.py
COPY data /app/data

# Expose port 8000 for the Gunicorn server to listen on
EXPOSE 8000

# Define the command to run your application using Gunicorn
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8000",  "--workers", "4"]
