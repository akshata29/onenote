# Runbook

## Chat incidents
- Symptom: Empty answers.
  - Check AI Search availability; query sample document in portal.
  - Validate `search-api-key` secret in Key Vault and app env.
  - Inspect Application Insights traces for `/chat` failures.

- Symptom: Missing citations.
  - Ensure `content_vector` populated during ingestion.
  - Re-run ingestion for affected notebook.

## Ingestion failures
- Look at Log Analytics query for `IngestionJobStatus` logs.
- Check Graph throttling: Graph returns 429; retry with backoff (configured in ingestion worker). Increase delay if frequent.

## Auth issues
- Verify SPA app redirect URI and API exposed scope `api://<api-id>/.default`.
- Confirm Key Vault secret `client-secret` matches API app credential.

## Deployment
- Redeploy containers with `az containerapp update --name <app> --image <image>`.
- Regenerate AI Search keys only if necessary; update Key Vault secret and restart backend.

## DR/Backup
- Storage account contains extracted artifacts; enable soft delete and versioning.
- AI Search can be rehydrated by re-running ingestion workflow.
