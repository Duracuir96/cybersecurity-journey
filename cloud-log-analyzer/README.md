># 🔍 Cloud Security Logs Analyzer & Dashboard

![Python](https://img.shields.io/badge/Python-3.8%2B-blue)
![Streamlit](https://static.streamlit.io/badges/streamlit_badge_black_white.svg)
![AWS](https://img.shields.io/badge/AWS-CloudTrail-orange)
![Pandas](https://img.shields.io/badge/Pandas-Data%20Analysis-green)

A real-time cloud security monitoring tool that analyzes AWS CloudTrail logs to detect suspicious activities and displays them in an interactive dashboard.

## ✨ Features

### 🎯 Core Features (MVP)
- **🔍 Log Analysis**: Automated collection and analysis of AWS CloudTrail logs
- **🚨 Threat Detection**: Identifies suspicious activities using heuristic rules
- **📊 Interactive Dashboard**: Real-time visualization with Streamlit
- **📧 Smart Alerts**: Email notifications for critical security events
- **☁️ Cloud Native**: Built with AWS serverless architecture in mind

### 🚀 Advanced Features (Roadmap)
- Machine Learning anomaly detection
- Multi-cloud support (Azure, GCP)
- Real-time alerting with Slack/Teams integration
- Containerized deployment with Docker

## 🛠️ Tech Stack

- **Backend**: Python 3.8+
- **Cloud**: AWS (CloudTrail, IAM, S3)
- **Data Processing**: Pandas, Boto3
- **Dashboard**: Streamlit
- **Alerting**: SMTPLib, AWS SNS

## 📸 Dashboard Preview


## 🚀 Quick Start

### Prerequisites
- Python 3.8 or higher
- AWS account with CloudTrail enabled
- AWS CLI configured with appropriate permissions

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/cloud-security-analyzer.git
   cd cloud-security-analyzer
   ```
2.  **Install dependencies**
   ```bash
pip install -r requirements.txt
   ``` 
3.  **Configure environment variables**
 ```bash
  cp .env.example .env
  # Edit .env with your AWS credentials and email settings
```
4.  **Run the dashboard**
 ```bash
  streamlit run src/dashboard.py
  ```
### Progress 
- create IAM user ✅
- Configured AWS CloudTrail to capture and retrieve AWS account activity logs✅
