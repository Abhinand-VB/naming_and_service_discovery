$ErrorActionPreference = "Stop"

Write-Host "=== Naming & Service Discovery Demo (Windows) ==="

if (!(Test-Path ".venv\\Scripts\\python.exe")) {
  Write-Host "Creating venv..."
  python -m venv .venv
}

Write-Host "Installing dependencies..."
& .\.venv\Scripts\python.exe -m pip install -r requirements.txt | Out-Null

Write-Host "Starting registry on http://localhost:5001 ..."
$registry = Start-Process -PassThru -WindowStyle Normal -FilePath .\.venv\Scripts\python.exe -ArgumentList @("service_registry_improved.py")
Start-Sleep -Seconds 2

Write-Host "Starting user-service instance 1 on http://localhost:8001 ..."
$svc1 = Start-Process -PassThru -WindowStyle Normal -FilePath .\.venv\Scripts\python.exe -ArgumentList @(
  "-m","src.user_service",
  "--port","8001",
  "--advertise","http://localhost:8001",
  "--registry-url","http://localhost:5001"
)

Write-Host "Starting user-service instance 2 on http://localhost:8002 ..."
$svc2 = Start-Process -PassThru -WindowStyle Normal -FilePath .\.venv\Scripts\python.exe -ArgumentList @(
  "-m","src.user_service",
  "--port","8002",
  "--advertise","http://localhost:8002",
  "--registry-url","http://localhost:5001"
)

Start-Sleep -Seconds 2

Write-Host "Running client (random calls)..."
& .\.venv\Scripts\python.exe -m src.client --service-name user-service --registry-url http://localhost:5001 --calls 8

Write-Host ""
Write-Host "Done. Stop processes if still running:"
Write-Host (" - registry PID: {0}" -f $registry.Id)
Write-Host (" - svc1 PID:     {0}" -f $svc1.Id)
Write-Host (" - svc2 PID:     {0}" -f $svc2.Id)

