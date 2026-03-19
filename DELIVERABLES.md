# Assignment Deliverables: Microservice Discovery

## Required

1. **Clean, working GitHub repo**
  - This repository (make sure your public repo includes the final code changes).
  - Grading commands are documented in `README.md`.
2. **Architecture diagram**
  - See [`ARCHITECTURE.md`](ARCHITECTURE.md) for:
    - A Mermaid diagram (recommended)
    - An ASCII fallback
3. **Demo video**
  - Record a short video (about 2–3 minutes) showing the required behavior:
    - Start **service registry**
    - Start **two instances** of the **same** service (`user-service`) on different ports
    - Run the **client** that:
      - discovers instances dynamically from the registry
      - randomly selects an instance for each call
  - Use `demo_script.md` as the narration + commands checklist.
  - Recommended helper command: `run_demo.ps1` (Windows).
  - Save the recording as [`Demo_Video.mp4`](Demo_Video.mp4) in the repo root (rename if your course expects a different filename).

## Evidence checklist (what the grader should observe)

- Registry logs show each instance **registering**.
- Client logs show multiple instances discovered and the field `chosen_instance` changing across calls.
- Client responses from the service endpoint (`/info`) clearly include instance identity (e.g., `port` and/or `instance_id`).

## Optional (Bonus): Service Mesh Discovery

If you extend this with Istio/Linkerd, the key concept is:

`App -> Sidecar Proxy -> Service Mesh`

Benefits to mention in your write-up:

- traffic routing
- observability
- security

