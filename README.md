# Naming & Service Discovery (Microservices + Registry)

This repo implements **client-side service discovery** using a simple **service registry** plus a microservice that **self-registers** and sends heartbeats. A client discovers available instances dynamically and **calls a RANDOM instance each time**.

This is designed to be **submission-ready** for the assignment:
- Run **2 instances** of the same service
- Services **register** with a registry
- Client **discovers** dynamically (no hardcoded instance list)
- Client **randomly selects** an instance per call

## What’s inside
- **Registry**: `service_registry_improved.py` (Flask, in-memory, heartbeats + cleanup)
- **Service**: `src/user_service.py` (Flask, `/info` shows instance identity, self-registers + heartbeats)
- **Client**: `src/client.py` (discovers instances and calls a RANDOM one per request)

## Architecture
See [`ARCHITECTURE.md`](ARCHITECTURE.md) for a Mermaid diagram and an ASCII fallback.

## Assignment Deliverables
See [`DELIVERABLES.md`](DELIVERABLES.md) for the full submission checklist.

1. **GitHub repo**: this repository.
2. **Architecture diagram**: see [`ARCHITECTURE.md`](ARCHITECTURE.md).
3. **Demo video**: record a 2–3 minute walkthrough using [`demo_script.md`](demo_script.md) (and optionally `run_demo.ps1`).
   - Save the recording as [`Demo_Video.mp4`](Demo_Video.mp4) in the repo root (rename if your course expects a different filename).

### What the demo must prove
- Two instances of the same service (`user-service`) are running on different ports.
- Both instances register with the registry and send heartbeats.
- The client discovers instances dynamically and **randomly selects** an instance on each call.
- Each client call response from `/info` clearly identifies which instance handled the request.

## Prerequisites
- Python 3.8+

## Quick start (Windows PowerShell)

### Option A: One command demo

```powershell
.\run_demo.ps1
```

### Option B: Manual steps (recommended for grading videos)

**1) Create venv + install**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**2) Start the registry**

```powershell
.\.venv\Scripts\python.exe service_registry_improved.py
```

**3) Start service instance 1**

```powershell
.\.venv\Scripts\python.exe -m src.user_service --port 8001 --advertise http://localhost:8001 --registry-url http://localhost:5001
```

**4) Start service instance 2**

```powershell
.\.venv\Scripts\python.exe -m src.user_service --port 8002 --advertise http://localhost:8002 --registry-url http://localhost:5001
```

**5) Run the client (random calls)**

```powershell
.\.venv\Scripts\python.exe -m src.client --service-name user-service --registry-url http://localhost:5001 --calls 8
```

## Expected output (proof of randomness)
In the client logs you should see `chosen_instance=` alternating between `http://localhost:8001` and `http://localhost:8002` across calls (random selection), and `/info` responses that include the instance identity:
- `{"service":"user-service","instance_id":"...","port":8001}`
- `{"service":"user-service","instance_id":"...","port":8002}`

## Demo video instructions
See `demo_script.md` for a tight 2–3 minute narration + commands + what output to show.

## Configuration (environment variables)
- **Registry**
  - `REGISTRY_PORT` (default `5001`)
  - `HEARTBEAT_TIMEOUT_SECONDS` (default `30`)
  - `CLEANUP_INTERVAL_SECONDS` (default `10`)
- **Service (`src/user_service.py`)**
  - `REGISTRY_URL` (default `http://localhost:5001`)
  - `SERVICE_PORT` (default `8001`)
  - `ADVERTISE_URL` (default computed)
  - `HEARTBEAT_INTERVAL_SECONDS` (default `5`)
  - `REGISTRY_WAIT_SECONDS` (default `15`)
- **Client (`src/client.py`)**
  - `REGISTRY_URL`, `TARGET_SERVICE`, `CALLS`, `CALL_PATH` (default `/info`)

## Screenshots (placeholders for submission)
- Add `docs/architecture.png` (optional screenshot of Mermaid diagram rendering)
- Add `docs/demo-output.png` (screenshot of client showing different chosen instances)

## 📚 What is a Service Registry?

A **Service Registry** is a database of available service instances in a distributed system. It enables:

- **Service Registration**: Services register themselves when they start
- **Service Discovery**: Services can find and communicate with each other
- **Health Monitoring**: Track which services are alive and healthy
- **Load Balancing**: Distribute requests across multiple service instances

## 🏗️ Architecture (high level)

```
┌─────────────┐         ┌─────────────────┐         ┌─────────────┐
│  Service A  │────────▶│ Service Registry │◀────────│  Service B  │
│ (Port 8001) │ Register│   (Port 5000)    │ Discover│ (Port 8002) │
└─────────────┘         └─────────────────┘         └─────────────┘
      │                          │                          │
      └──────── Heartbeat ───────┘                          │
                                 └──────── Heartbeat ───────┘
```

## 📁 Project Files (selected)

### 1. `service_registry.py` (Original Example)
The basic implementation you provided - simple but functional.

**Pros:**
- ✅ Simple and easy to understand
- ✅ Core functionality works

**Cons:**
- ❌ No error handling
- ❌ No health checks
- ❌ No way to remove services
- ❌ Services stay registered forever (even if they crash)

### 2. `service_registry_improved.py` (Production-Ready)
Enhanced version with enterprise features.

**New Features:**
- ✅ **Error Handling**: Proper validation and error responses
- ✅ **Health Checks**: Heartbeat mechanism to detect dead services
- ✅ **Deregistration**: Services can unregister gracefully
- ✅ **Auto Cleanup**: Removes stale services automatically
- ✅ **Thread Safety**: Uses locks for concurrent access
- ✅ **Detailed Responses**: Rich JSON responses with metadata
- ✅ **Service Listing**: View all registered services

### 3. `src/user_service.py`
The microservice implementation used for grading: runs HTTP + self-registers + heartbeats.

### 4. `src/client.py`
Discovers instances dynamically and calls a **RANDOM** instance per request.

### 5. `example_service.py` (legacy)
Kept for backwards compatibility with earlier learning scripts; the new graded path is `src/`.

### 4. Kubernetes/Minikube Deployment
- **Dockerfile** - Container image for the registry
- **k8s/** - Kubernetes manifests for deployment
- **KUBERNETES.md** - Complete Kubernetes deployment guide
- **deploy-minikube.sh** - Automated deployment script

### 5. HashiCorp Consul Integration
- **consul_client.py** - Consul service discovery client
- **CONSUL.md** - Production-grade service registry guide
- Compare custom implementation with industry-standard Consul

## 🚀 Getting Started

Choose your learning path:

### Option 1: Local Development (Recommended for Learning)

#### Prerequisites

Python 3.8 or higher

#### Installation

1. **Clone the repository:**
```bash
git clone https://github.com/ranjanr/ServiceRegistry.git
cd ServiceRegistry
```

2. **Create a virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

#### Running the Registry

**Basic Version:**
```bash
python3 service_registry.py
```

**Improved Version (Recommended):**
```bash
python3 service_registry_improved.py
```

The registry will start on `http://localhost:5001`

### Option 2: Kubernetes/Minikube (Production-like Environment)

#### Prerequisites

- [Minikube](https://minikube.sigs.k8s.io/docs/start/)
- [kubectl](https://kubernetes.io/docs/tasks/tools/)
- Docker

#### Quick Deploy

```bash
# One-command deployment
./deploy-minikube.sh
```

This will:
1. Start Minikube (if not running)
2. Build Docker image
3. Deploy registry and example services
4. Show access URLs and test commands

#### Manual Deploy

```bash
# Start Minikube
minikube start

# Build image
eval $(minikube docker-env)
docker build -t service-registry:latest .

# Deploy
kubectl apply -f k8s/registry-deployment.yaml
kubectl apply -f k8s/example-service-deployment.yaml

# Access
minikube ip  # Get IP
curl http://<MINIKUBE_IP>:30001/health
```

**See [KUBERNETES.md](KUBERNETES.md) for complete guide.**

### Testing with the graded microservice + client
Use the “Manual steps” section above (or `run_demo.ps1`).

## 📡 API Endpoints

### 1. Register a Service
```http
POST /register
Content-Type: application/json

{
  "service": "user-service",
  "address": "http://localhost:8001"
}
```

**Response:**
```json
{
  "status": "registered",
  "message": "Service user-service registered at http://localhost:8001"
}
```

### 2. Discover a Service
```http
GET /discover/user-service
```

**Response:**
```json
{
  "service": "user-service",
  "instances": [
    {
      "address": "http://localhost:8001",
      "uptime_seconds": 45.2
    }
  ],
  "count": 1
}
```

### 3. Send Heartbeat
```http
POST /heartbeat
Content-Type: application/json

{
  "service": "user-service",
  "address": "http://localhost:8001"
}
```

### 4. Deregister a Service
```http
POST /deregister
Content-Type: application/json

{
  "service": "user-service",
  "address": "http://localhost:8001"
}
```

### 5. List All Services
```http
GET /services
```

**Response:**
```json
{
  "services": {
    "user-service": {
      "total_instances": 2,
      "active_instances": 2
    },
    "payment-service": {
      "total_instances": 1,
      "active_instances": 1
    }
  },
  "total_services": 2
}
```

### 6. Health Check
```http
GET /health
```

## 🔍 Key Concepts Explained

### 1. Service Registration
When a service starts, it tells the registry:
- **Who am I?** (service name)
- **Where am I?** (address/port)

```python
# Service registers itself
requests.post("http://registry:5001/register", json={
    "service": "user-service",
    "address": "http://localhost:8001"
})
```

### 2. Service Discovery
When a service needs to call another service:
- Ask the registry for available instances
- Get list of addresses
- Choose one (**RANDOM** for this assignment)

```python
# Discover payment service
response = requests.get("http://registry:5001/discover/payment-service")
instances = response.json()['instances']
payment_url = instances[0]['address']  # Use first instance
```

### 3. Heartbeat Mechanism
Services periodically send "I'm alive" signals:
- Prevents stale entries
- Detects crashed services
- Registry removes services that stop sending heartbeats

```python
# Send heartbeat every 10 seconds
while True:
    requests.post("http://registry:5001/heartbeat", json={
        "service": "user-service",
        "address": "http://localhost:8001"
    })
    time.sleep(10)
```

### 4. Graceful Shutdown
When a service stops, it should deregister:
- Prevents clients from calling dead services
- Keeps registry clean

```python
# On shutdown
requests.post("http://registry:5001/deregister", json={
    "service": "user-service",
    "address": "http://localhost:8001"
})
```

## 🎯 Real-World Use Cases

### Netflix Eureka
Netflix uses a similar pattern with their Eureka service registry:
- Microservices register on startup
- Other services discover them dynamically
- Handles thousands of service instances

### Kubernetes Service Discovery
Kubernetes has built-in service discovery:
- Services register via DNS
- Load balancing across pods
- Health checks and auto-restart

### Consul by HashiCorp
Production-grade service registry with:
- Health checking
- Key-value store
- Multi-datacenter support

## 🔧 Improvements You Could Add

1. **Persistence**: Save registry to disk/database
2. **Load Balancing**: Return instances in round-robin order
3. **Service Metadata**: Store version, tags, capabilities
4. **Authentication**: Secure the registry endpoints
5. **Monitoring**: Add metrics and logging
6. **Clustering**: Multiple registry instances for high availability
7. **Service Mesh**: Integrate with Istio or Linkerd

## (Bonus) How this extends to a Service Mesh (Istio/Linkerd)
In a service mesh, discovery/routing is typically handled by sidecars and control plane components:

`App → Sidecar Proxy → Service Mesh`

Benefits:
- **Traffic routing**: retries, timeouts, weighted routing, canary releases
- **Observability**: distributed tracing, metrics, request logs
- **Security**: mTLS between services, policy enforcement

## 🧪 Testing with cURL

```bash
# Register a service
curl -X POST http://localhost:5001/register \
  -H "Content-Type: application/json" \
  -d '{"service": "test-service", "address": "http://localhost:9000"}'

# Discover services
curl http://localhost:5001/discover/test-service

# List all services
curl http://localhost:5001/services

# Send heartbeat
curl -X POST http://localhost:5001/heartbeat \
  -H "Content-Type: application/json" \
  -d '{"service": "test-service", "address": "http://localhost:9000"}'

# Deregister
curl -X POST http://localhost:5001/deregister \
  -H "Content-Type: application/json" \
  -d '{"service": "test-service", "address": "http://localhost:9000"}'
```

## 📊 Comparison: Original vs Improved

| Feature | Original | Improved |
|---------|----------|----------|
| Registration | ✅ | ✅ |
| Discovery | ✅ | ✅ |
| Error Handling | ❌ | ✅ |
| Heartbeats | ❌ | ✅ |
| Deregistration | ❌ | ✅ |
| Auto Cleanup | ❌ | ✅ |
| Thread Safety | ❌ | ✅ |
| Service Listing | ❌ | ✅ |
| Health Endpoint | ❌ | ✅ |
| Uptime Tracking | ❌ | ✅ |

## 🎓 Learning Resources

- **Microservices Patterns** by Chris Richardson
- **Building Microservices** by Sam Newman
- **Martin Fowler's Blog**: https://martinfowler.com/articles/microservices.html

## 📝 License

This is a learning project - feel free to use and modify as needed!

## 🤝 Contributing

This is an educational project. Feel free to:
- Add new features
- Improve documentation
- Create additional examples
- Share your learnings!