# Demo Video Script (2–3 minutes)

## Goal (what the demo proves)
- Two instances of the **same** microservice are running.
- Both instances **self-register** with a registry.
- A client **discovers instances dynamically** (no hardcoded service URLs).
- The client **randomly selects** an instance on each call, and the response shows which instance handled it.

---

## Narration (read this)

Hi, this is a quick demo of **service discovery with a custom service registry**.

I’m going to start a registry, then start **two instances of the same service** (`user-service`) on different ports.
Each instance registers itself with the registry and sends heartbeats.

Finally, I’ll run a client that queries the registry, gets the list of instances, and **randomly calls one instance each time**.
You’ll see the called instance change across requests because selection is random, and each response includes the instance’s identity.

---

## Commands to run (Windows PowerShell)

### Option A: One-command demo (recommended)

```powershell
.\run_demo.ps1
```

### Option B: Manual steps (show these in the video)

**1) Create venv + install deps**

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

**2) Start registry**

```powershell
.\.venv\Scripts\python.exe service_registry_improved.py
```

**3) Start user-service instance 1**

```powershell
.\.venv\Scripts\python.exe -m src.user_service --port 8001 --advertise http://localhost:8001 --registry-url http://localhost:5001
```

**4) Start user-service instance 2**

```powershell
.\.venv\Scripts\python.exe -m src.user_service --port 8002 --advertise http://localhost:8002 --registry-url http://localhost:5001
```

**5) Run client (random calls)**

```powershell
.\.venv\Scripts\python.exe -m src.client --service-name user-service --registry-url http://localhost:5001 --calls 8
```

---

## What to show on screen (expected output)

### In each service terminal
- A log line confirming registration, e.g. “registered … http://localhost:8001”
- Heartbeat logs continuing periodically

### In the client terminal
- Logs showing it discovered multiple instances
- Logs showing `chosen_instance=...` changing across calls
- Responses from `/info` including `instance_id` and `port`

---

## Expected result (explain this)
- The client does **not** have service instance URLs hardcoded.
- On each call, the client asks the registry for instances and uses:
  - `random.choice(instances)` (random selection per call)
- The `/info` response proves which instance handled the request.

