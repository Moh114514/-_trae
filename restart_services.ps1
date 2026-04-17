# BEIMS Service Restart Script (Enhanced Version)
# Usage: .\restart_services.ps1

$ErrorActionPreference = "Stop"

Write-Host ""
Write-Host "========================================"
Write-Host "  BEIMS Service Restart Tool"
Write-Host "========================================"
Write-Host ""

$projectDir = "e:\openclaw-project\workspace\Fuwu"
# Dynamically find frontend directory to avoid encoding issues
$frontendDir = (Get-ChildItem $projectDir -Directory | Where-Object { $_.Name -like "BEIMS*" }).FullName
if (-not $frontendDir) {
    Write-Host "[ERROR] Frontend directory not found!"
    exit 1
}

Write-Host "[INFO] Project: $projectDir"
Write-Host ""

# Step 1: Stop all Python processes
Write-Host "[1/4] Stopping existing services..."
try {
    $pythonProcs = Get-Process python -ErrorAction SilentlyContinue
    if ($pythonProcs) {
        $pythonProcs | Stop-Process -Force -ErrorAction Stop
        Write-Host "     [OK] Stopped $($pythonProcs.Count) Python process(es)"
    } else {
        Write-Host "     [INFO] No running Python processes"
    }
} catch {
    Write-Host "     [WARN] Error stopping processes: $_"
}
Start-Sleep -Seconds 3

# Step 2: Clean old logs (optional)
try {
    if (Test-Path "$projectDir\api_log.txt") {
        Remove-Item "$projectDir\api_log.txt" -ErrorAction SilentlyContinue
        Remove-Item "$projectDir\api_err.txt" -ErrorAction SilentlyContinue
        Write-Host "[2/4] Cleaned old log files"
    } else {
        Write-Host "[2/4] No logs to clean"
    }
} catch {
    Write-Host "[2/4] [WARN] Error cleaning logs: $_"
}

# Step 3: Start frontend service (port 8081) - with retry
Write-Host "[3/4] Starting frontend service (port 8081)..."
$frontendStarted = $false
$maxRetries = 3

# Convert frontendDir to absolute path to avoid encoding issues
$frontendAbsPath = (Resolve-Path $frontendDir -ErrorAction SilentlyContinue).Path
if (-not $frontendAbsPath) {
    Write-Host "     [WARN] Frontend directory not found: $frontendDir"
} else {
    for ($i = 1; $i -le $maxRetries; $i++) {
        try {
            # Method 1: Use Start-Process with full path and explicit working dir
            $pythonExe = (Get-Command python).Source
            $proc = New-Object System.Diagnostics.Process
            $proc.StartInfo.FileName = $pythonExe
            $proc.StartInfo.Arguments = "-m http.server 8081"
            $proc.StartInfo.WorkingDirectory = $frontendAbsPath
            $proc.StartInfo.WindowStyle = "Normal"
            $proc.Start() | Out-Null
            
            Start-Sleep -Seconds 3
            
            # Verify it's running
            $frontendCheck = netstat -ano | findstr ":8081" | findstr "LISTENING"
            if ($frontendCheck) {
                Write-Host "     [OK] Frontend service started (attempt $i)"
                $frontendStarted = $true
                break
            } else {
                Write-Host "     [WARN] Attempt $i failed, port not listening"
                if ($i -lt $maxRetries) {
                    Write-Host "     Retrying in 2 seconds..."
                    Start-Sleep -Seconds 2
                }
            }
        } catch {
            Write-Host "     [ERROR] Attempt $i failed: $_"
            if ($i -lt $maxRetries) {
                Start-Sleep -Seconds 2
            }
        }
    }
}

if (-not $frontendStarted) {
    Write-Host "     [ERROR] Frontend failed to start after $maxRetries attempts"
    Write-Host "     Trying fallback method..."
    
    # Fallback: Use cmd.exe to avoid PowerShell path encoding issues
    try {
        $cmdArgs = "/c cd /d `"$frontendAbsPath`" && python -m http.server 8081"
        Start-Process -FilePath "cmd.exe" `
            -ArgumentList $cmdArgs `
            -WindowStyle Normal
        Start-Sleep -Seconds 3
        
        $fallbackCheck = netstat -ano | findstr ":8081" | findstr "LISTENING"
        if ($fallbackCheck) {
            Write-Host "     [OK] Frontend started via fallback method"
            $frontendStarted = $true
        }
    } catch {
        Write-Host "     [ERROR] Fallback also failed: $_"
    }
}

# Step 4: Start backend API service (port 8082)
Write-Host "[4/4] Starting backend API service (port 8082)..."
Write-Host "     Loading Embedding model, please wait..."

try {
    $pythonExe = (Get-Command python).Source
    Start-Process -FilePath $pythonExe `
        -ArgumentList "api_server.py" `
        -WorkingDirectory $projectDir `
        -RedirectStandardOutput "$projectDir\api_log.txt" `
        -RedirectStandardError "$projectDir\api_err.txt" `
        -WindowStyle Hidden `
        -ErrorAction Stop
    
    Write-Host "     Backend process started, waiting for initialization..."
} catch {
    Write-Host "     [ERROR] Failed to start backend: $_"
}

# Wait for backend to fully start
$maxWait = 35
$waited = 0
$backendStarted = $false
while ($waited -lt $maxWait) {
    Start-Sleep -Seconds 2
    $waited += 2
    try {
        $backendCheck = netstat -ano | findstr ":8082" | findstr "LISTENING"
        if ($backendCheck) {
            $backendStarted = $true
            break
        }
    } catch {}
    
    # Show progress every 10 seconds
    if ($waited % 10 -eq 0) {
        Write-Host "     ... still waiting (${waited}s / ${maxWait}s)"
    }
}

# Final status check
Write-Host ""
Write-Host "========================================"
if ($frontendStarted -and $backendStarted) {
    Write-Host "  All Services Started Successfully!"
} else {
    Write-Host "  Service Startup Completed (with warnings)"
}
Write-Host "========================================"
Write-Host ""

$p1 = netstat -ano | findstr ":8081" | findstr "LISTENING"
$p2 = netstat -ano | findstr ":8082" | findstr "LISTENING"
$p3 = netstat -ano | findstr ":11434" | findstr "LISTENING"

Write-Host "Service Status:"
if ($p1) { Write-Host "   [OK] Frontend (HTTP Server)   - Port 8081" } else { Write-Host "   [FAIL] Frontend NOT running!" }
if ($p2) { Write-Host "   [OK] Backend API (FastAPI)     - Port 8082" } else { Write-Host "   [FAIL] Backend API NOT running!" }
if ($p3) { Write-Host "   [OK] Ollama Local Model        - Port 11434" } else { Write-Host "   [WARN] Ollama not running" }

Write-Host ""
Write-Host "Access URLs:"
Write-Host "   - Frontend: http://localhost:8081"
Write-Host "   - API Docs: http://localhost:8082/docs"
Write-Host ""

if (-not $p2) {
    Write-Host "[WARN] Backend may need more time. Check logs:"
    Write-Host "   $projectDir\api_err.txt"
    Write-Host ""
}

if (-not $frontendStarted) {
    Write-Host "[TROUBLESHOOTING] Frontend not running. Manual fix:"
    Write-Host "   cd '$frontendDir'"
    Write-Host "   python -m http.server 8081"
    Write-Host ""
}

Write-Host "[INFO] Press Ctrl+C to exit (services will keep running)"
Write-Host ""
