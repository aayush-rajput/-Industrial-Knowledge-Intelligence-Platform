$ErrorActionPreference = "Stop"
Write-Host "Downloading Neo4j Community 5.20.0..."
Invoke-WebRequest -Uri "https://dist.neo4j.org/neo4j-community-5.20.0-windows.zip" -OutFile "neo4j.zip"
Write-Host "Extracting..."
Expand-Archive -Path "neo4j.zip" -DestinationPath "neo4j" -Force
cd neo4j\neo4j-community-5.20.0\bin
Write-Host "Setting initial password to 'password'..."
.\neo4j-admin.bat dbms set-initial-password password
Write-Host "Starting Neo4j Console..."
.\neo4j.bat console
