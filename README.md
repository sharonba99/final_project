# URL Shortener Project

This project is a full-stack URL shortening application with a complete DevOps infrastructure. 
It features a microservices architecture deployed on Minikube using Terraform and Kubernetes.

---

## Project Structure
```
├── backend
│   ├── app.py
│   ├── Dockerfile
│   ├── requirements.txt
│   └── test_app.py
├── docker-compose.yaml
├── frontend
│   ├── Dockerfile
│   ├── index.html
│   ├── nginx.conf
│   ├── package.json
│   ├── package-lock.json
│   ├── src
│   │   ├── App.css
│   │   ├── App.jsx
│   │   └── main.jsx
│   └── vite.config.js
├── jenkins
│   ├── Jenkinsfile
│   └── jenkins-kubeconfig.yaml
├── kubernetes
│   ├── backend
│   │   ├── configmap.yaml
│   │   ├── deployment.yaml
│   │   ├── hpa.yaml
│   │   ├── secret.yaml
│   │   └── service.yaml
│   ├── database
│   │   ├── secret.yaml
│   │   ├── service.yaml
│   │   └── statefulset.yaml
│   ├── frontend
│   │   ├── configmap.yaml
│   │   ├── deployment.yaml
│   │   ├── hpa.yaml
│   │   └── service.yaml
│   ├── ingress
│   │   └── ingress.yaml
│   ├── monitoring
│   │   ├── grafana
│   │   │   ├── clusterrole.yaml
│   │   │   ├── configmap.yaml
│   │   │   ├── dashboards
│   │   │   ├── deployment.yaml
│   │   │   └── service.yaml
│   │   └── prometheus
│   │       ├── clusterrole.yaml
│   │       ├── configmap.yaml
│   │       ├── deployment.yaml
│   │       └── service.yaml
│   └── namespaces
│       └── namespace.yaml
├── README.md
└── terraform
    ├── main.tf
    ├── modules
    │   └── k8s-infra
    │       ├── main.tf
    │       ├── outputs.tf
    │       └── variables.tf
    └── outputs.tf
```

## Local Development Environment

### 1. Prerequisites
* **Minikube** installed
  ```powershell
      # MacOs
      brew install minikube
      
      # Linux 
       curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
       sudo install minikube-linux-amd64 /usr/local/bin/minikube

      # Windows
      choco install minikube
  ```
* **Helm** (for Monitoring Stack)
* **Terraform** executable

### 2. Infrastructure (Terraform)
We use Terraform Workspaces to manage environment-specific resources.

```powershell
cd devops-infra/terraform
./terraform init
./terraform workspace select dev
./terraform apply -auto-approve
```
---

Build and Deployment
Build and Load Images
Since we are using Minikube, images must be built locally and loaded into the node:

```powershell
# Build Backend
cd backend-api
docker build -t sharonba/url-shortener-backend:latest .
minikube image load sharonba/url-shortener-backend:latest

# Build Frontend
cd ../frontend-app
docker build -t sharonba/url-shortener-frontend:latest .
minikube image load sharonba/url-shortener-frontend:latest
```
---

Kubernetes Manifests
Apply the manifests to the cluster in the required order:

```powershell
cd kubernetes
kubectl create namespace urlshortener
kubectl apply -f . -R -n urlshortener
```
---

Monitoring Stack
The project includes a monitoring stack based on Prometheus and Grafana to track application performance.

Installation
```powershell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
```

Key Metrics Tracked
Request Rate: HTTP requests per second (p50,p95,p99).
Active backend pods.
System Health: CPU and Memory usage per pod.

Access Information
Application UI: http://urlshortener.local
Metrics Endpoint: http://urlshortener.local/api/metrics
Grafana Access: Run kubectl port-forward svc/monitoring-stack-grafana 3000:80 -n monitoring and visit http://localhost:3000
