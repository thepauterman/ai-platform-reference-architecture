@echo off
for /f "delims=" %%i in ('gcloud auth print-identity-token') do set TOKEN=%%i
curl -H "Authorization: Bearer %TOKEN%" https://ai-governance-gateway-3jffhamrba-uc.a.run.app/health