# Part 1: Problem Description and Cloud

## 1. Problem Description

**The Context:**

Spain's rapid expansion of renewable energy has led to a critical challenge in its electrical grid known as the "Duck Curve" or "Cannibalization Effect." During peak daylight hours (especially in high-irradiance regions like Extremadura), the massive generation of photovoltaic (PV) energy often outpaces the national energy demand. This oversupply frequently drives the wholesale electricity market prices (managed by OMIE) to zero or even **negative values**. 

**The Problem:**

When market prices drop below zero, solar plant operators literally have to pay money to inject their generated electricity into the grid. A static, batch-processed monitoring system is too slow to react to these market fluctuations, resulting in significant daily financial losses for the asset owners.

**The Solution:**

This project solves this issue by building a **Real-Time Streaming Pipeline and Digital Twin** for a simulated utility-scale solar plant in Badajoz, Spain. 

The architecture leverages event-driven data engineering to perform **Algorithmic Energy Trading**. It continuously ingests live weather forecasts (via the *Open-Meteo API*) and real-time market prices (via the *ESIOS API*). By processing this unbounded data stream using **Apache Kafka** and **PySpark Structured Streaming**, the system dynamically calculates the plant's physical power output (using `pvlib`) and executes automated business logic in real-time:

1. **Smart Curtailment:** Automatically flagging the system to halt grid injection when market prices turn negative, preventing financial penalties.

2. **BESS Arbitrage (Battery Energy Storage System):** Diverting the curtailed energy to a battery system, allowing the plant to discharge and sell the stored energy later during the night when demand and prices peak.

Ultimately, this pipeline transforms raw meteorological and financial data streams into autonomous, revenue-saving operational decisions.

## 2. Cloud & Infrastructure as Code (IaC)

This project is developed in the cloud using **Google Cloud Platform (GCP)**. To ensure reproducibility, scalability, and automated provisioning of the environment, **Terraform** is utilized as the Infrastructure as Code (IaC) tool.

The Terraform configuration files (`main.tf` and `variables.tf`) are designed to automatically provision the necessary storage and analytics resources for the pipeline—specifically, the Data Lake (Google Cloud Storage) and the Data Warehouse (BigQuery), which will act as the final sink for our streaming data.

#### Deployment Workflow

**Step 1: Project & Repository Setup**

1. Clone this repository to your local environment.
2. Ensure you have an active GCP Project created.
3. Update the `variables.tf` file with your specific GCP `project_id` and desired region settings.

**Step 2: Authentication**

In order for Terraform to create resources in your GCP account, it requires the appropriate permissions. Authenticate your local environment via the Google Cloud CLI by executing the following command in your terminal:

```bash
gcloud auth application-default login
```

**Step 3: Infrastructure Provisioning**

*Technical Note (Working Directory):* Terraform is designed to look for configuration files (`.tf`) exclusively in the current working directory. If you run Terraform commands from the root of the project, it will result in an error. You must execute them from inside the infrastructure folder.

Navigate to the terraform directory:

```bash
cd terraform
```

Execute the standard Terraform lifecycle commands sequentially (wait for each to finish before launching the next):

1. **Initialize the working directory:** This downloads the necessary Google Cloud providers defined at the top of your configuration files.
   ```bash
   terraform init
   ```

2. **Review the execution plan:** This reads your code and outputs a summary of the infrastructure to be built. You should see a message indicating that 2 resources will be added.
   ```bash
   terraform plan
   ```

3. **Apply the configuration:** This deploys the infrastructure to GCP. The terminal will prompt you for a final confirmation. Type `yes` and press Enter.
   ```bash
   terraform apply
   ```

### 🏗️ Architecture Overview
The project follows an **Edge-to-Cloud** architecture:
- **Edge (Local/Mac Studio):** Real-time physics simulation (Digital Twin), Message Brokering (Kafka), and Local Analytics (TimescaleDB + Grafana).
- **Cloud (GCP):** Long-term cold storage (GCS) and Data Warehousing (BigQuery) orchestrated via Terraform.

---

### 🟢 Sprint 1: The Physical Digital Twin (Python & Physics)
Development of a high-fidelity simulation script (`gemelo_digital.py`) that models a real PV plant in **Badajoz, Spain**.

- **Physical Modeling:** Implemented using `pvlib`, utilizing the **CEC Module database** (Canadian Solar 400W) and **Sandia Inverter database** (SMA Sunny Central).
- **Live Data Ingestion:** - Real-time weather data (DNI, DHI, Temp, Wind) via **Open-Meteo API**.
    - Spot market prices (€/MWh) via **ESIOS OMIE API**.
- **Edge Logic:** Continuous 60-second loop calculating Plane of Array (POA) irradiance and AC power output based on real-time environmental conditions.

### 🔵 Sprint 2: Streaming Infrastructure (Docker & Kafka)
Deployment of the local processing backbone using a containerized environment optimized for macOS.

- **Orchestration:** Transitioned from Docker Desktop to **OrbStack** for high-performance, low-latency container management.
- **Components:**
    - **Apache Kafka (KRaft):** Single-node cluster for high-throughput message streaming without Zookeeper overhead.
    - **TimescaleDB:** Time-series optimized PostgreSQL for storing generation and pricing logs.
    - **Grafana:** Real-time dashboarding for the Digital Twin's telemetry.
- **Health Checks:** Implemented `depends_on` conditions and automated health checks to ensure sub-second reliability between services.

---

## 🛠️ Tech Stack
- **Languages:** Python (Pandas, pvlib, Requests).
- **Infrastructure:** Docker, OrbStack, Terraform.
- **Streaming:** Apache Kafka.
- **Storage:** TimescaleDB, Google Cloud Storage, BigQuery.
- **Observability:** Grafana.

## 🔜 Next Steps (Sprint 3)
- Developing the **PySpark Structured Streaming** engine to implement the "Smart Curtailment" logic: automatically shutting down virtual inverters when market prices turn negative to protect revenue.
