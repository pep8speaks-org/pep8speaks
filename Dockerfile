# Use an official Python runtime as a parent image
FROM python:3.8-alpine

# install PDM
RUN pip install -U pip setuptools wheel
RUN pip install pdm

# copy files
COPY pyproject.toml pdm.lock README.md /project/

COPY . /project


WORKDIR /project

RUN pdm install

EXPOSE 8000

# Define the command to run your application using Gunicorn
CMD ["pdm", "run", "start"]
