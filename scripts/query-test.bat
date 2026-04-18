@echo off
for /f "delims=" %%i in ('gcloud auth print-identity-token') do set TOKEN=%%i
curl -X POST -H "Authorization: Bearer %TOKEN%" -H "Content-Type: application/json" -d "{\"prompt\": \"hello\", \"user_id\": \"test-user\"}" https://ai-governance-gateway-3jffhamrba-uc.a.run.app/query