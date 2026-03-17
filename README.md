# Task Automation & Job Tracking System (Python CLI)

[![Jenkins CI/CD](https://img.shields.io/badge/Jenkins-CI%2FCD-blue.svg?logo=jenkins)](https://www.jenkins.io/)
[![Docker](https://img.shields.io/badge/Docker-Containerized-2496ED.svg?logo=docker)](https://www.docker.com/)
[![Ansible](https://img.shields.io/badge/Ansible-Deployed-EE0000.svg?logo=ansible)](https://www.ansible.com/)
[![Python 3.10](https://img.shields.io/badge/Python-3.10-3776AB.svg?logo=python)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-Database-4479A1.svg?logo=mysql)](https://www.mysql.com/)

A scalable, containerized Python Command Line Interface (CLI) application for adding, tracking, and executing system tasks. It features built-in execution retries, persistent logging, and a complete end-to-end automated Continuous Integration and Continuous Deployment (CI/CD) pipeline.

## 🏗 System Architecture

This project was built to demonstrate full-stack DevOps automation:

1. **Python CLI Application:** Built using `click` and `rich`, it allows users to schedule bash commands.
2. **Execute & Retry Engine:** Uses `subprocess` to run commands with timeout and robust retry capabilities.
3. **Persistent Database:** Uses `MySQL` to store tasks, their execution status (`PENDING`, `RUNNING`, `SUCCESS`, `FAILED`), and robust log output.
4. **Pytest Testing Suite:** Contains 29 automated unit tests verifying the CRUD operations and execution logic.
5. **Docker Containerization:** Application and databases are isolated using a multi-stage `Dockerfile` and `docker-compose.yml`.
6. **Jenkins CI/CD:** A complete `Jenkinsfile` pipeline that automatically installs dependencies, runs tests, builds the Docker image, and pushes it to Docker Hub on every commit.
7. **Ansible Automation:** An Ansible playbook (`deploy.yml`) that securely logs into the production server, manages network configuration, cleans old data, and deploys the latest containers.

---

## 🚀 Getting Started

The easiest way to run this project is natively via Docker natively inside its customized network.

### 1. Initial Setup (Local Development)
If you wish to spin up the source code locally for development:
```bash
# Clone the repository
git clone https://github.com/Mohit1-cmd/Python_TaskScheduler.git
cd Python_TaskScheduler

# Spin up the Database and the Python App locally
docker-compose up -d --build
```

### 2. Enter the CLI Container
Once the container environment is running (either locally or via the Ansible CI/CD deployment), hop into the interactive Python container:
```bash
docker exec -it task-cli bash
```

---

## 💻 CLI Usage Guide

From inside the `task-cli` container, use the `cli.py` script to interact with the task scheduler:

### Global Help Menu
```bash
python cli.py --help
```

### 1. Add a Task
Add a bash command to the queue. It will be stored in MySQL with a `PENDING` status.
```bash
python cli.py add "echo Hello World!"
python cli.py add "ls -la"
```

### 2. List All Tasks
View a beautifully formatted table of all tasks, their statuses, and retry counts.
```bash
python cli.py list
```

### 3. Run a Task
Execute a task by its ID. You can specify instantaneous retries in case of temporary network or command failures.
```bash
python cli.py run 1
python cli.py run 2 --retries 5
```

### 4. View Task Execution Logs
View the direct standard output (stdout) and standard error (stderr) of a completed task.
```bash
python cli.py logs 1
```

### 5. Check Specific Task Status
Quickly poll the exact execution status and timestamps of a single task.
```bash
python cli.py status 1
```

### 6. Retry All Failed Tasks
Search the database for all tasks with a `FAILED` status and attempt to run them again. This increments the macro-retry database counter.
```bash
python cli.py retry-failed
```

---

## 🛠 CI/CD Pipeline Flow

This repository contains a full `Jenkinsfile`. On every push to `main`, Jenkins will automatically:
1. Checkout the source code.
2. Create a virtual environment and install `requirements.txt`.
3. Execute `pytest tests/ -v`.
4. If tests pass, build a new Docker image from the `Dockerfile`.
5. Authenticate and push the new image to Docker Hub (`mohit67/task-automation-cli:latest`).
6. Execute the `ansible/deploy.yml` playbook.
7. Ansible connects to the server, tears down the old environment, sets up the `task-network`, initializes an empty MySQL `taskdb` using `/docker-entrypoint-initdb.d/init_db.sql`, and deploys the newly built image.

---
*Built for Software Production Engineering (SPE)*
