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
│   │   │   |   ├── app-dashboard.yaml
|   |   |   |   ├── k8s-dashboard.yaml
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
    ├── backend.tf
    ├── variables.tf
    └── outputs.tf
```

## Local Development Environment

## Prerequisites
* **Minikube** 
  ```powershell
      # MacOs
      brew install minikube
      minikube start
  
      # Linux 
      curl -LO https://storage.googleapis.com/minikube/releases/latest/minikube-linux-amd64
      sudo install minikube-linux-amd64 /usr/local/bin/minikube
      minikube start

      # Windows
      choco install minikube
      minikube start
  ```
     ```
      In order to access the URL you need to add it to /etc/hosts
      First do the command minikube ip and put the output IP address in the file:
      192.168.9.1 urlshortener.local
     ```

## Terraform
We use Terraform Workspaces to manage environment-specific resources.

```powershell
cd devops-infra/terraform
terraform init
kubectl delete namespace urlshortener # Making sure the namespace is removed since applying creates the namespace again.
terraform apply -auto-approve
```


## Build and Deployment
Since we are using Minikube, images must be built locally and loaded into the node:

```powershell
# Build Backend
cd backend
docker build -t sharonba/url-shortener-backend:latest .
minikube image load sharonba/url-shortener-backend:latest

# Build Frontend
cd ../frontend
docker build -t sharonba/url-shortener-frontend:latest .
minikube image load sharonba/url-shortener-frontend:latest
```
---

## Kubernetes Manifests
Apply the manifests to the cluster in the required order:

```powershell
cd kubernetes
kubectl create namespace urlshortener
kubectl apply -f . -R -n urlshortener
```

## Monitoring Stack
The project includes a monitoring stack based on Prometheus and Grafana to track application performance.

```
Access the Grafana dashboard by going to urlshortener.local:32000
To access the Prometheus UI first port forward port 9090 with the command
kubectl port-forward deploy/prometheus-deployment 9090:9090 -n urlshortener
and then go to localhost:9090
```
```powershell
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring-stack prometheus-community/kube-prometheus-stack --namespace monitoring --create-namespace
```

