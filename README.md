# Autonomous AI Agent

A Python-based autonomous AI agent that accepts natural language requests, plans tasks, executes them, and generates professional Word (.docx) documents.

Built with FastAPI, LangChain, python-docx, and three AI providers: **Google AI Studio**, **NVIDIA NIM**, and **Mistral AI**.

## Architecture

![Architecture](diagrams/architecture.png)

## Agent Workflow

```
User Request
     │
     ▼
Planner ──► Generator ──► Reflection ──► DOCX Builder
(Google)    (NVIDIA)       (Google)       (python-docx)
                │               │
                ▼               ▼
           Fallback          Optional
           (Mistral)         Regeneration
```

## Folder Structure

```
project/
  app.py                  FastAPI application with routes
  config.py               Environment variables and settings
  requirements.txt        Dependencies
  README.md               This file
  generated_docs/         Output .docx files
  agent/
    planner.py            Task planning with structured output
    executor.py           Single-pass full document generation
    reflector.py          Quality review and self-check
    workflow.py           Orchestrates the full pipeline
  prompts/
    planner_prompt.py     Prompt template for planning
    executor_prompt.py    Prompt template for full document generation
    reflection_prompt.py  Prompt template for quality review
  services/
    llm.py                LLM factory (create_llm + get_provider_info + extract_text)
    retry.py              Retry with exponential backoff + jitter
    performance.py        Performance tracker and instrumentation
    document_generator.py python-docx document builder (parses # headings)
  models/
    request.py            Request schema
    response.py           Response schema
    planner_output.py     Planner output schema
```

## Installation

```bash
cd project
pip install -r requirements.txt
```

## Environment Variables

Create a `.env` file in the `project/` directory:

```
GEMINI_API_KEY=your_gemini_api_key_here
NVIDIA_API_KEY=your_nvidia_api_key_here
MISTRAL_API_KEY=your_mistral_api_key_here
```

At least one API key is required. The `primary_model` and `fallback_model` in `config.py` determine which provider is used.

Get free API keys at:
- [Google AI Studio](https://makersuite.google.com/app/apikey)
- [NVIDIA NIM](https://build.nvidia.com)
- [Mistral AI](https://console.mistral.ai/api-keys/)

## Running Locally

```bash
uvicorn app:app --reload
```

The API will be available at `http://localhost:8000`.

## API

### POST /agent

Accepts a natural language request and returns a structured response with a generated document.

**Request:**

```json
{
  "request": "Write a project proposal for a customer loyalty mobile app for a retail chain with 50 stores. Include budget estimates and timeline."
}
```

**Response:**

```json
{
  "tasks": [
    { "id": 1, "description": "Define project objectives" },
    { "id": 2, "description": "Outline scope and deliverables" }
  ],
  "assumptions": [
    "Assuming a budget of $50,000-$100,000",
    "Assuming 50 stores across the region"
  ],
  "summary": "Generated Project Proposal: Customer Loyalty Mobile App with 6 sections based on 5 planned tasks.",
  "document_path": "generated_docs/project_proposal_customer_loyalty_20260704_143022.docx",
  "execution_log": [
    { "step": "Planning", "status": "success", "details": "Identified 5 tasks, 2 assumptions, 6 sections" },
    { "step": "Execution", "status": "success", "details": "Generated 6 sections" },
    { "step": "Reflection", "status": "success", "details": "All sections meet quality standards." },
    { "step": "Document Generation", "status": "success", "details": "Saved to generated_docs/..." }
  ]
}
```

### GET /

Returns API information and available endpoints.

### GET /health

Returns `{ "status": "healthy" }`.

## Example Requests

### Standard Request

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"request": "Write a project proposal for a customer loyalty mobile app for a retail chain with 50 stores. Include budget estimates and timeline."}'
```

### Complex Request

```bash
curl -X POST http://localhost:8000/agent \
  -H "Content-Type: application/json" \
  -d '{"request": "I need a document for our team quarterly review. We missed our targets last quarter. Revenue was down 15%. Make it professional but honest. I am not sure what sections to include."}'
```

## Engineering Feature: Reflection / Self-Check

The reflector module (`agent/reflector.py`) implements a self-check mechanism:

1. After the full document is generated, the reflector sends the entire document to the LLM for review
2. The LLM checks for professionalism, grammar, missing sections, consistency, assumptions, and completeness
3. If the document meets standards (PASS), it proceeds to DOCX generation
4. If improvement is needed (IMPROVED), the **entire document is regenerated once** with the feedback incorporated
5. Maximum 4 LLM calls: Plan → Generate → Reflect → Optional one regeneration

This replaces the previous per-section regeneration with single-pass full-document regeneration, ensuring consistency across all sections while keeping the pipeline fast.

## Engineering Decisions

- **Pipeline architecture** over dynamic agent loops: Predictable, debuggable, easy to trace failures
- **Single-pass document generation** over per-section generation: 6x faster, fewer LLM calls, consistent tone/style across sections
- **PydanticOutputParser** for structured planning output: No regex parsing, type-safe, clean
- **Multi-provider support**: Google/NVIDIA/Mistral — switch by changing model name in config
- **Dependency injection**: Components receive `llm` via parameter, never call `create_llm()` themselves
- **Retry with exponential backoff**: Transient errors (429/5xx/timeout) retried up to 2 times with jitter
- **Provider fallback**: If primary fails after retries, automatically switches to fallback provider
- **Sequential execution**: Sections generated one at a time to avoid rate limit errors
- **Quality scoring**: Reflection assigns a 1-10 score and identifies weak sections
- **Instrumentation**: Every LLM call logs provider, model, duration, prompt/response size, retries

## Provider Architecture

The system supports three AI providers, switched by model name prefix:

| Prefix | Provider | Example Model |
|--------|----------|---------------|
| `nvidia/` | NVIDIA NIM | `nvidia/nemotron-3-ultra-550b-a55b` |
| `mistral` | Mistral AI | `mistral-large-latest` |
| (anything else) | Google AI Studio | `gemma-4-31b-it` |

Set `primary_model` and `fallback_model` in `config.py` to any combination.

## Tradeoffs

| Choice | Benefit | Cost |
|--------|---------|------|
| Pipeline vs Agent Loop | Predictable, debuggable | Less flexible for open-ended tasks |
| Single-pass vs Per-section | 6x faster, consistent tone, fewer API calls | Less granular control per section |
| Multi-provider | Provider flexibility | Multiple API keys needed |
| Retry + fallback | Resilient to API outages | Slightly slower on failure |
| Single-pass execution | Single LLM call, fast, consistent | Longer per-call context window needed |
| Single-pass reflection | Simple, fast | May miss subtle issues |

## Future Improvements

- Streaming responses for real-time progress tracking
- Multi-agent architecture for complex cross-document workflows
- RAG integration for company-specific knowledge and templates
- Conversation memory for iterative document refinement
- Web search tool for up-to-date research during generation
- Parallel section-level generation with batched API calls for even faster execution
