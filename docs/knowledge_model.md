# Civora AI — Knowledge Model Specification

This specification details how regulatory and government compliance knowledge is ingested, structured, versioned, and retrieved by Civora AI without modifying core codebase files.

---

## 1. Regulatory Knowledge Representation

To build an adaptable compliance platform, government regulations are decomposed into modular configuration blocks. Rather than hardcoding state compliance logic into Python code, the knowledge engine abstracts law into two parallel representations:

1. **Relational Metadata Schema**: Captures structured constraints (fees, processing durations, age requirements, residency requirements) linked to specific jurisdictions and license nodes.
2. **Semantic Vector Store (Unstructured)**: Captures unstructured explanatory text, exceptions, and footnotes from gazettes and official circulars to ground the AI conversational replies.

---

## 2. Ingestion Pipeline: Regulations to Structured Data

The transformation of textual government law into system knowledge follows a three-stage ingestion process:

```
+--------------------+      +--------------------+      +--------------------+
|  1. Document Stage | ---> | 2. Extraction Stage| ---> |  3. Ingest Stage   |
|   (Gazette PDFs)   |      |  (Gemini Parse)    |      | (PostgreSQL &      |
|                    |      |                    |      |  Qdrant Vectors)   |
+--------------------+      +--------------------+      +--------------------+
```

### Stage 1: Document Stage (Raw Input)
* Raw gazette notifications, government portal PDFs, and municipal booklets are stored in `data/raw/`.
* Source documents are stamped with metadata including `state_code`, `issuing_authority`, `effective_date`, and `document_id`.

### Stage 2: Extraction Stage (AI-Guided Parsing)
* Using the Google Gemini API with strict Pydantic structured output settings, source texts are parsed to extract:
  * Compliance parameters (fees, renewal periods, required attachments).
  * Node connections (which business types require which licenses).
* Textual sections are sliced into overlapping chunks (e.g. 500 characters with 100-character overlap) preserving section numbers (e.g., "Section 12(b)").

### Stage 3: Ingestion Stage (Database Writes)
* Extract parameters are committed to the Relational Database (representing the **Knowledge Graph** links).
* Chunked texts are passed through an embedding model (e.g. `sentence-transformers`) and committed to Qdrant Vector DB, tagged with metadata filters:
  ```json
  {
    "document_id": "DE-LLC-REG-2026",
    "state": "DE",
    "section": "Section 18-201",
    "authority": "Division of Corporations"
  }
  ```

---

## 3. AI Retrieval Model

When a user triggers the advisory chat, query resolution runs a hybrid search:

```
 User Query: "What are the fees for Delaware LLC?"
                         |
      +------------------+------------------+
      |                                     |
      v (Vector Search)                     v (Structured Query)
Qdrant: Semantic Retrieval           Postgres: Direct Lookup
(Matches "Certificate Fee")          (Matches Fee Node where State='DE')
      |                                     |
      +------------------+------------------+
                         |
                         v
       Context Aggregator & Sanitizer
                         |
                         v
      Gemini API: Prompt Grounding & Output
```

1. **Structured Query Routing**: The NLP layer parses metadata attributes (e.g., `State = Delaware`, `Topic = LLC Fee`). The repository fetches exact attributes from the database (e.g., fee node value `$90`).
2. **Semantic Vector Matching**: Simultaneously, Qdrant searches for relevant statutory descriptions matching "Delaware LLC setup fees".
3. **Prompt Grounding**: The exact relational parameters and textual quotes are combined into a system instruction context:
   ```
   SYSTEM INSTRUCTION: You are a government compliance mentor. Answer using ONLY the context provided below. Citing sources is mandatory.
   CONTEXT:
   - Relational Fee Node: $90
   - Retrieved Statutory Quote: "Delaware Certificate of Formation filing fee is $90." (DE-LLC-REG-2026, Sec. 101)
   ```
4. **Structured Generation**: Gemini formats the response to the user, appending citations.

---

## 4. Code-Free Regulation Expansion

To scale across new states, districts, and industries without rewrites, Civora AI isolates operational logic from data configurations. 

Adding a new state (e.g., Texas LLC registration) requires only generating a JSON configuration file inside the knowledge tree:
```json
{
  "state_code": "TX",
  "business_type": "LLC",
  "steps": [
    {
      "step_number": 1,
      "task": "File Certificate of Formation (Form 205)",
      "authority": "Texas Secretary of State",
      "fee": 300.00,
      "document_requirements": ["Registered Agent Consent Form"]
    }
  ]
}
```
At boot time or via admin trigger, the Knowledge Engine parses these files and automatically populates the graph database relations, making the new state path instantly discoverable to the registration wizard and the RAG model.

---

## 5. Versioning Strategy

Regulatory laws change. Some dates are adjusted, and some fees increase. To maintain transactional history and prevent system breakage for active applications, we apply **Temporal Versioning**:

* **Bi-temporal Schema**: Every knowledge node and edge record includes `valid_from` and `valid_to` timestamps.
* **Non-destructive Updates**: When a fee changes (e.g. Delaware LLC fee rises from $90 to $100):
  * The existing fee node is not updated. Its `valid_to` field is set to the current date (e.g., `2026-06-25`).
  * A new fee record is inserted with `valid_from = 2026-06-26` and `value = 100.00`.
* **State Preservation**: Users who filed *before* the change reference the historical node (matching their application submission timestamp), while new applicants automatically query the active node.
* **Embedding Invalidation**: Updates flag old document chunks as `inactive` in the vector database to prevent old guidelines from bleeding into active RAG prompts.
