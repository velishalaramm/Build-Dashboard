# DevOps Deployment Dashboard

A centralized deployment dashboard built using [Flask](https://flask.palletsprojects.com?utm_source=chatgpt.com) and integrated with [Jenkins](https://www.jenkins.io?utm_source=chatgpt.com), [Amazon EC2](https://aws.amazon.com/ec2/?utm_source=chatgpt.com), and SVN repositories to automate Java and .NET application deployments. The application provides secure multi-user login, deployment monitoring, live logs, deployment history, and AWS server management through a simple web interface. 

## Features

* Secure multi-user authentication
* Trigger Jenkins deployments from UI
* Support for Java and .NET applications
* AWS EC2 server start/stop integration
* Real-time deployment status tracking
* Live Jenkins console log viewing
* Deployment history dashboard
* API key-based security
* User activity logging with IP tracking
* CORS-enabled backend APIs

## Technology Stack

* Backend: Python Flask
* CI/CD: Jenkins
* Cloud: AWS EC2
* Version Control: SVN / GitHub
* Logging: Python Logging Module
* API Communication: REST APIs
* Authentication: API Key & User Credentials

## Supported Applications

### Java Applications

* Cart
* Payment

### .NET Applications

* Wishlist



## Core Functionalities

### Deployment Automation

Users can trigger deployments directly from the dashboard by selecting:

* Technology type
* Application name
* Deployment type
* SVN repository URL

The system automatically triggers the corresponding Jenkins job and monitors the build status.

### AWS Server Monitoring

The dashboard checks AWS EC2 instance status before login and allows users to start servers when required.

### Deployment Monitoring

* Real-time build status
* Jenkins console logs
* Deployment history tracking
* Daily deployment count statistics

## Security

* API key validation
* Multi-user authentication
* Environment variable-based secret management
* Access logging with IP address tracking

## Environment Variables Required

```env
JENKINS_URL=
USER=
TOKEN=
API_KEY=
AWS_ACCESS_KEY=
AWS_SECRET_KEY=
AWS_REGION=
INSTANCE_1_ID=
INSTANCE_2_ID=
APP_USER=
APP_PASS=
USERS_LIST=
```

## Run the Application

```bash
pip install -r requirements.txt
python app.py
```

## API Endpoints

| Endpoint             | Description             |
| -------------------- | ----------------------- |
| `/api/login`         | User login              |
| `/api/logout`        | User logout             |
| `/api/start-servers` | Start AWS EC2 instances |
| `/api/deploy`        | Trigger deployment      |
| `/api/status`        | Check deployment status |
| `/api/logs`          | View Jenkins logs       |
| `/api/history`       | Deployment history      |

## Use Case

This project is designed for DevOps teams to simplify and centralize deployment operations for enterprise applications hosted on AWS infrastructure with Jenkins CI/CD pipelines.
