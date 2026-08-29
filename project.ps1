param(
    [ValidateSet("help", "scaffold", "venv", "install", "setup", "demo", "pipeline", "run", "check", "tree", "clean", "clean-data")]
    [string]$Action = "help",
    [string]$Csv = ""
)

$ErrorActionPreference = "Stop"
$ProjectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ProjectRoot

$VenvPath = Join-Path $ProjectRoot ".venv"
$VenvPython = Join-Path $VenvPath "Scripts\python.exe"
$VenvPip = Join-Path $VenvPath "Scripts\pip.exe"
$Streamlit = Join-Path $VenvPath "Scripts\streamlit.exe"

$ProjectDirectories = @(
    "data\raw",
    "data\processed",
    "src\brand_visibility",
    "src\brand_visibility\analytics",
    "src\brand_visibility\dashboard",
    "src\brand_visibility\data",
    "tests"
)

$PackageFiles = @(
    "data\raw\.gitkeep",
    "data\processed\.gitkeep",
    "src\brand_visibility\__init__.py",
    "src\brand_visibility\analytics\__init__.py",
    "src\brand_visibility\dashboard\__init__.py",
    "src\brand_visibility\data\__init__.py",
    "tests\__init__.py"
)

function Show-Help {
    Write-Host "Brand Visibility Intelligence - PowerShell commands"
    Write-Host ""
    Write-Host "  .\project.ps1 scaffold"
    Write-Host "  .\project.ps1 setup"
    Write-Host "  .\project.ps1 demo"
    Write-Host "  .\project.ps1 pipeline -Csv data\raw\brand_dataset.csv"
    Write-Host "  .\project.ps1 run"
    Write-Host "  .\project.ps1 check"
    Write-Host "  .\project.ps1 tree"
    Write-Host "  .\project.ps1 clean"
    Write-Host "  .\project.ps1 clean-data"
}

function New-Scaffold {
    foreach ($Directory in $ProjectDirectories) {
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    }
    foreach ($File in $PackageFiles) {
        if (-not (Test-Path $File)) {
            New-Item -ItemType File -Path $File | Out-Null
        }
    }
    Write-Host "Project scaffold is ready."
}

function New-VirtualEnvironment {
    if (-not (Test-Path $VenvPython)) {
        $PythonCommand = Get-Command py -ErrorAction SilentlyContinue
        if ($PythonCommand) {
            & py -3 -m venv $VenvPath
        }
        else {
            $PythonCommand = Get-Command python -ErrorAction SilentlyContinue
            if (-not $PythonCommand) {
                throw "Python was not found. Install Python 3 and enable 'Add Python to PATH'."
            }
            & python -m venv $VenvPath
        }
    }
    Write-Host "Virtual environment is ready at $VenvPath"
}

function Install-Project {
    New-VirtualEnvironment
    & $VenvPython -m pip install --upgrade pip
    & $VenvPython -m pip install -e .
}

function Assert-Installed {
    if (-not (Test-Path $VenvPython)) {
        throw "Virtual environment not found. Run: .\project.ps1 setup"
    }
}

switch ($Action) {
    "help" {
        Show-Help
    }
    "scaffold" {
        New-Scaffold
    }
    "venv" {
        New-VirtualEnvironment
    }
    "install" {
        Install-Project
    }
    "setup" {
        New-Scaffold
        Install-Project
        Write-Host "Setup complete. Run '.\project.ps1 demo' and then '.\project.ps1 run'."
    }
    "demo" {
        Assert-Installed
        New-Scaffold
        & $VenvPython -m brand_visibility.pipeline --demo
    }
    "pipeline" {
        Assert-Installed
        if ([string]::IsNullOrWhiteSpace($Csv)) {
            throw "CSV path required. Example: .\project.ps1 pipeline -Csv data\raw\brand_dataset.csv"
        }
        if (-not (Test-Path $Csv -PathType Leaf)) {
            throw "CSV file was not found: $Csv"
        }
        & $VenvPython -m brand_visibility.pipeline --csv $Csv
    }
    "run" {
        Assert-Installed
        & $Streamlit run app.py
    }
    "check" {
        Assert-Installed
        & $VenvPython -m compileall -q src app.py
        & $VenvPython -m brand_visibility.pipeline --demo
        & $VenvPython -c "from brand_visibility.config import DATABASE; from brand_visibility.data.load import load_from_database; d=load_from_database(DATABASE); assert len(d)>0; assert {'brand','visibility_score','price_range','discount_pct'} <= set(d.columns); print('Checks passed:', len(d), 'products')"
    }
    "tree" {
        Get-ChildItem -Force -Recurse |
            Where-Object { $_.FullName -notmatch '[\\/](\.git|\.venv|__pycache__)([\\/]|$)' } |
            ForEach-Object { $_.FullName.Replace($ProjectRoot, ".") }
    }
    "clean" {
        Get-ChildItem -Directory -Recurse -Filter "__pycache__" -ErrorAction SilentlyContinue |
            Remove-Item -Recurse -Force
        Get-ChildItem -File -Recurse -Include "*.pyc", "*.pyo" -ErrorAction SilentlyContinue |
            Remove-Item -Force
        @("build", "dist", ".pytest_cache") | ForEach-Object {
            if (Test-Path $_) { Remove-Item $_ -Recurse -Force }
        }
        Write-Host "Python build and cache files removed."
    }
    "clean-data" {
        @(
            "data\processed\brand_visibility_clean.csv",
            "data\processed\brand_visibility.db",
            "data\processed\eda_summary.json"
        ) | ForEach-Object {
            if (Test-Path $_) { Remove-Item $_ -Force }
        }
        Write-Host "Generated data removed."
    }
}
