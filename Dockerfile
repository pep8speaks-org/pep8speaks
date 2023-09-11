# Use an official Python runtime as a parent image
FROM python:3.8-slim

# Set the working directory to /app
WORKDIR /app

# Copy the current directory contents into the container at /app
COPY . /app

# Install any needed packages specified in requirements.txt
RUN pip install -r requirements.txt

# Expose port 8000 for the Gunicorn server to listen on
EXPOSE 5000

# Define the command to run your application using Gunicorn
CMD ["gunicorn", "server:app", "--bind", "0.0.0.0:8000"]
