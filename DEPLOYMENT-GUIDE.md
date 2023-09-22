# Deployment Guide

This guide covers deploying the pep8speaks server on any Linux-based machine.

System Requirements
-------------------
The current server is hosted on a DO droplet with the following specs:

- 512 MB RAM
- 1 CPU General purpose shared CPU

and is able to handle the current load of ~100 req/minute. 

Deployment Steps
----------------

- We use `docker` and `docker-compose` to deploy the project. Install them from [here](https://docs.docker.com/engine/install/).
- For Ubunut 22.04 LTS run the following command
  ```
  apt update
  apt install -y docker.io
  apt install -y docker-compose
  ```
- Clone the pep8speaks project or copy the `docker-compose.yml` and `.env.sample` files.
- Make a `.env` file by copying the `.env.sample` and populate the environment variable.
- Run the following command:
  ```
  # This command starts the pep8speaks container
  docker-compose up -d
  # This command can be used to see the health
  docker-compose ps
  # Check logs using
  docker-compose logs -f --tail 100
  ```
- Get a domain name pointed to the IP of the server and add `HTTPS` by following this tutorial: https://www.digitalocean.com/community/tutorials/initial-server-setup-with-ubuntu-20-04

