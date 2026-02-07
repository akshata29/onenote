# Architecture

```
+--------------------+        +---------------------------+
|      React SPA     |<------>| Azure API Management (opt)|
|  MSAL auth (SPA)   |        +---------------------------+
| Mode toggle (MCP/AI|                     |
| Search)            |                     v
+---------+----------+          +------------------+
          | OBO JWT               |  FastAPI API   |
          v                       |  (Container App|
+----------------------+          |   / AppSvc)    |
| Foundry Agent Service|          +------------------+
| + Workflow (chat,    |                  |
|   ingestion)         |                  v
+----------+-----------+      +------------------------+
           | tools              | Azure Container Apps |
           |                    |  - MCP server        |
           |                    |  - Attach extractor  |
           |                    +------------------------+
           v                               |
+----------------------+                    v
| Azure AI Search      |<---embeddings---+-------+
| (vector + semantic)  |                  |Azure  |
+----------------------+                  |OpenAI |
           ^                             +-------+
           | indexed chunks                       
           v                                      
+----------------------+     +-------------------+
| Azure Storage (Blob) |<--->| Doc Intelligence  |
+----------------------+     +-------------------+
           ^
           | raw content
           v
+----------------------+
| Microsoft Graph      |
| OneNote delegated    |
+----------------------+
```
