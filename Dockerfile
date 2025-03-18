# Use an official Python runtime as a parent image
FROM python:3.8-alpine

# Set the working directory to /app
WORKDIR /app

# Install UV
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY uv.lock pyproject.toml /app/

COPY pep8speaks /app/pep8speaks
COPY server.py /app/server.py
COPY data /app/data

# Expose port 8000 for the Gunicorn server to listen on
EXPOSE 8000

# Define the command to run your application using Gunicorn
CMD ["uv", "run", "gunicorn", "server:app", "--bind", "0.0.0.0:8000",  "--workers", "4"]
