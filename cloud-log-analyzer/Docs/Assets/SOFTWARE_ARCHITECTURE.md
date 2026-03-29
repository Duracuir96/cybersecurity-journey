# 🏗️ Architecture 4+1 – AWS CloudTrail Log Analyzer

---

# 1️⃣ Logical View

### 🎯 Objective

Describe **business concepts**, **responsibilities**, and their **relationships**, independently of any technical or deployment considerations.

### 📐 Associated Diagram

✅ **UML Class Diagram**

---

### 🧩 Class Diagram – PlantUML
<div align="center">
  <img width="374" height="600" alt="image" src="https://github.com/user-attachments/assets/c13f27d1-1290-4330-b0ad-e431cd7b3809" />
</div>


---

# 2️⃣ Development View

### 🎯 Objective

Show **code organization**, **modules**, and their **dependencies**, as seen by developers.

### 📐 Associated Diagram

✅ **UML Component Diagram**

---

### 🧩 Component Diagram – PlantUML

<img width="493" height="476" alt="image" src="https://github.com/user-attachments/assets/17c57afd-caa1-4485-95e7-09a320676f58" />


```text
aws-cloudtrail-log-analyzer/
│
├── app/                          # Main application
│   ├── main.py                   # Streamlit entry point
│   │
│   ├── data_collection/          # Data collection
│   │   ├── __init__.py
│   │   └── aws_connector.py      # CloudTrail connection (Boto3)
│   │
│   ├── data_processing/          # Parsing & cleaning
│   │   ├── __init__.py
│   │   ├── parser.py             # JSON → DataFrame
│   │   └── validator.py          # Validation & cleaning
│   │
│   ├── security_analysis/        # Security analysis
│   │   ├── __init__.py
│   │   ├── heuristics.py         # Detection rules
│   │   └── statistics.py         # Global statistics
│   │
│   ├── visualization/            # Dashboard & graphics
│   │   ├── __init__.py
│   │   ├── dashboard.py          # Streamlit layout
│   │   └── charts.py             # Bar charts, tables
│   │
│   ├── alerting/                 # Alerting system
│   │   ├── __init__.py
│   │   └── email_notifier.py     # SMTP / Gmail
│   │
│   └── config/                   # Global configuration
│       ├── __init__.py
│       └── settings.py           # Environment variables
│
├── tests/                        # Unit tests
│   ├── test_aws_connector.py
│   ├── test_parser.py
│   ├── test_heuristics.py
│   └── test_email_notifier.py
│
├── .gitignore                    # Exclude secrets / venv
├── requirements.txt              # Python dependencies
├── README.md                     # Project documentation
└── LICENSE
```

---

# 3️⃣ Process View

### 🎯 Objective

Describe **runtime dynamic behavior** of the system:

- processing order
- component interactions
- alerting logic

### 📐 Associated Diagram

✅ **UML Sequence Diagram**

---

### 🧩 Sequence Diagram – PlantUML

<img width="750" height="512" alt="image" src="https://github.com/user-attachments/assets/08d6f11e-9e07-4c77-9863-6c158a7a9997" />

---

# 4️⃣ Physical View

### 🎯 Objective

Show **where the system runs**, on which **nodes**, and how they communicate.

### 📐 Associated Diagram

✅ **UML Deployment Diagram**

---

### 🧩 Deployment Diagram – PlantUML

<img width="509" height="283" alt="image" src="https://github.com/user-attachments/assets/07b13dad-c92d-4638-a7cc-b4913eb26920" />

---

# 5️⃣ Use Case View (+1)

### 🎯 Objective

Link **business needs** to system functionalities from the user's perspective.

### 📐 Associated Diagram

✅ **UML Use Case Diagram**

---

### 🧩 Use Case Diagram – PlantUML
<img width="412" height="345" alt="image" src="https://github.com/user-attachments/assets/b3ec193d-f180-4c3d-83c2-eb398b04e8ab" />


---

#  Final Summary (Strictly Compliant)

| View | UML Diagram |
|------|-------------|
| Logical View | Class Diagram |
| Development View | Component Diagram |
| Process View | Sequence Diagram |
| Physical View | Deployment Diagram |
| Use Case View (+1) | Use Case Diagram |

---

# 1 **Key Architectural Decisions**

1. **Modular / Decoupled Architecture**
   - Each module is independent:
     - `data_collection`, `data_processing`, `security_analysis`, `visualization`, `alerting`
   - Facilitates **maintainability**, **unit testing**, **scalability**
   - Decision motivated by **Separation of Concerns**
2. **Cloud-Native / Serverless**
   - Deployment on **Streamlit Cloud**
   - Access logs via **AWS CloudTrail API**
   - No dedicated server, no persistent local database
   - Simplifies **horizontal scalability** and **secret management** (via environment variables)
3. **Sequential Processing Pipeline**
   - Logs → Parsing → Validation → Heuristic Analysis → Dashboard / Alerts
   - Enables a **clear and traceable workflow**
   - Decision motivated by business logic: analyze events **in order for reliability**
4. **Credential Security**
   - Use of **environment variables** for AWS and SMTP
   - No hardcoded secrets
   - Decision motivated by **DevSecOps security**
5. **Lightweight Interactive Web Interface**
   - Use of **Streamlit** for a reactive dashboard
   - Decision motivated by:
     - Rapid development
     - Cloud accessibility
     - Simplicity for admins
6. **Simple Yet Effective Alerting**
   - Predefined thresholds (>10 login failures, etc.)
   - SMTP alerts
   - Decision motivated by **operational efficiency**, prioritizing simplicity
7. **Extensibility**
   - The pipeline allows adding:
     - new heuristic rules
     - new visualizations
     - external storage (S3, RDS, or Elasticsearch)

---

# 2 **Probable Design Patterns**

| **Pattern** | **Usage in the Project** | **Rationale** |
|-------------|--------------------------|---------------|
| **Singleton** | AWSConnector, EmailNotifier | Ensure **a single instance of AWS / SMTP connection** |
| **Facade** | DashboardUI | Hide pipeline processing complexity behind a simple interface |
| **Observer / Event Listener** | Alerting | Automatically trigger an alert when a critical condition is met |
| **Strategy** | HeuristicEngine | Allow easy addition of different detection strategies (failed logins, IAM changes, policy changes) |
| **Builder** | LogParser + DataValidator | Build clean DataFrames from JSON step by step |
| **Template Method** | Log Analysis | Define generic flow: parse → validate → analyze → visualize, with ability to extend certain steps |
| **Adapter** | AWS / Streamlit Integration | Adapt CloudTrail JSON output to Pandas/dashboard expected format |
| **Composite** (optional) | Visualization | Combine multiple charts/widgets in the dashboard as a hierarchy |

---

# 3 **Justification**

- **Separation of Concerns** → minimizes side effects and makes the system testable
- **Structuring Patterns (Singleton, Facade)** → simplify code and maintenance
- **Behavioral Patterns (Observer, Strategy, Template)** → flexible for detection rules and alerting
- **Adaptation Patterns (Adapter, Composite)** → facilitate integration and future evolution

---

 **Summary:**

- The project is **modular, secure, scalable, and cloud-native**
- The **chosen patterns** maximize **maintainability, reusability, and readability**
- The pipeline is **clearly defined and extensible** for future features (ML, centralized storage, advanced notifications)
