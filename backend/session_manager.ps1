#!/usr/bin/env pwsh

$BASE_URL = "http://localhost:3000/project_mystery_backend/0.1.0/sessions"
$SESSION_NAME = "test_session"
$SESSION_ID = "Oq_AZ99Zh7RZEtEP"

function Print-Usage {
    Write-Host "Usage: $($MyInvocation.ScriptName) [--create_session | --load_session | --unload_session | --reset_session]"
    exit 1
}

function Create-Session {
    Write-Host "Creating session..."
    curl.exe -s -X POST "$BASE_URL/" -H "Content-Type: application/json" -d "{`"session_name`": `"$SESSION_NAME`"}"
    Write-Host "`nDone."
}

function Load-Session {
    Write-Host "Loading session..."
    curl.exe -s -X POST "$BASE_URL/$SESSION_ID/load"
    Write-Host "`nDone."
}

function Unload-Session {
    Write-Host "Unloading session..."
    curl.exe -s -X POST "$BASE_URL/unload"
    Write-Host "`nDone."
}

function Reset-Session {
    Write-Host "Resetting session..."
    curl.exe -s -X POST "$BASE_URL/$SESSION_ID/reset"
    Write-Host "`nDone."
}

if ($args.Count -eq 0) {
    Print-Usage
}

switch ($args[0]) {
    "--create_session"  { Create-Session }
    "--load_session"    { Load-Session }
    "--unload_session"  { Unload-Session }
    "--reset_session"   { Reset-Session }
    default             { Print-Usage }
}