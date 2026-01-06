# Novel Polisher Backend Build Script
# This script builds the Python backend into a standalone executable

param(
    [switch]$Clean = $false
)

$ErrorActionPreference = "Stop"

Write-Host "=== Novel Polisher Backend Build ===" -ForegroundColor Cyan

# Get script directory
$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $scriptDir

# Clean if requested
if ($Clean) {
    Write-Host "Cleaning previous build..." -ForegroundColor Yellow
    if (Test-Path "dist") { Remove-Item -Recurse -Force "dist" }
    if (Test-Path "build") { Remove-Item -Recurse -Force "build" }
    if (Test-Path "*.spec") { Remove-Item -Force "*.spec" }
}

# Check Python
Write-Host "Checking Python installation..." -ForegroundColor Yellow
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "ERROR: Python not found. Please install Python 3.10+ and add to PATH." -ForegroundColor Red
    exit 1
}

# Install dependencies
Write-Host "Installing dependencies..." -ForegroundColor Yellow
pip install -r requirements.txt --quiet
if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: Failed to install dependencies" -ForegroundColor Red
    exit 1
}

# Build with PyInstaller
Write-Host "Building executable with PyInstaller..." -ForegroundColor Yellow

$pyinstallerArgs = @(
    "--onefile",
    "--name", "backend",
    "--console",
    "--collect-all", "google.generativeai",
    "--collect-all", "google.cloud",
    "--collect-all", "vertexai",
    "--collect-all", "google.api_core",
    "--hidden-import", "google.generativeai",
    "--hidden-import", "google.cloud.aiplatform",
    "--hidden-import", "vertexai",
    "--hidden-import", "vertexai.generative_models",
    "--add-data", "style.yaml;.",
    "--add-data", "glossary.json;.",
    "src/main.py"
)

pyinstaller @pyinstallerArgs

if ($LASTEXITCODE -ne 0) {
    Write-Host "ERROR: PyInstaller build failed" -ForegroundColor Red
    exit 1
}

# Verify output
$exePath = Join-Path $scriptDir "dist\backend.exe"
if (Test-Path $exePath) {
    $size = (Get-Item $exePath).Length / 1MB
    Write-Host ""
    Write-Host "=== Build Successful ===" -ForegroundColor Green
    Write-Host "Output: $exePath" -ForegroundColor Cyan
    Write-Host "Size: $([math]::Round($size, 2)) MB" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Test with: .\dist\backend.exe --help" -ForegroundColor Yellow
} else {
    Write-Host "ERROR: backend.exe not found after build" -ForegroundColor Red
    exit 1
}
