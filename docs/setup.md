# Setup

1. **Prereqs**
   - Azure subscription + Owner rights to deploy.
   - Node 20+, Python 3.11+, Azure CLI, Bicep CLI.
   - Create two Entra app registrations: SPA (frontend) and API (backend) with delegated Graph Notes.Read, Notes.Read.All. Configure redirect URI to `http://localhost:5173/`.

2. **Deploy infra**
   ```bash
   cd infra
   az deployment group create -g <rg> -f main.bicep -p namePrefix=onenoterag tenantId=<tenant> backendImage=<acr>/backend:latest mcpImage=<acr>/mcp:latest openAiName=<openai>
   ```

3. **Provision AI Search index**
   - Create index `onenote-index` with fields from docs (id, content, content_vector, notebook_id, section_id, page_id, page_title, page_url, source_type, attachment_name, modified_time, tenant_id, user_id, chunk_id, chunk_offset).

4. **Configure Key Vault secrets**
   - `client-secret` (API app secret)
   - `search-api-key` (Search admin key)
   - `openai-api-key` (Azure OpenAI key)

5. **Backend local dev**
   ```bash
   cd backend
   cp ../.env.sample .env
   uvicorn app.main:app --reload
   ```

6. **Frontend local dev**
   ```bash
   cd frontend
   cp .env.sample .env
   npm install
   npm run dev
   ```

7. **Foundry Agent + Workflow**
   - Import `backend/agents/onenote_agent.yaml` and `backend/workflows/ingestion_workflow.yaml` into Foundry.
   - Point tools to deployed API endpoints and MCP container app URL.

8. **MCP server deployment**
   - Build MCP server image based on referenced repos, publish to ACR, set env vars (Graph client id/secret, tenant).

9. **Observability**
   - Connect Application Insights to Log Analytics; enable OTLP export to Azure Monitor.

10. **CI/CD**
    - Use `.github/workflows/ci.yml` for lint/build/tests; add deployment stage per environment.
