# Test Cases – Autonomous AI Agent

This document contains sample requests for testing the Autonomous AI Agent API.

Endpoint:

```
POST /agent
```

Request Format:

```json
{
  "request": "..."
}
```

---

# Test Case 1 – Standard Business Request

## Description

Generate a professional project proposal for a software project.

### Request

```json
{
  "request": "Create a professional project proposal for developing a customer loyalty mobile application for a retail chain with around 50 stores. Include an executive summary, project objectives, scope, proposed solution, implementation timeline, estimated budget, risks, recommendations, and conclusion."
}
```

### Expected Behaviour

The agent should:

- Create its own execution plan
- Generate a structured TODO list
- Make reasonable assumptions
- Produce a complete business proposal
- Review the generated document
- Export a formatted Microsoft Word (.docx) document

---

# Test Case 2 – Complex Ambiguous Request

## Description

A vague request requiring autonomous reasoning and assumptions.

### Request

```json
{
  "request": "Our company had a difficult quarter. Revenue dropped by nearly 15%, several projects were delayed, and employee morale has been affected. I need a professional document for senior management explaining the current situation, possible causes, recommendations for recovery, and an action plan. I am not sure what sections should be included, so decide the structure yourself and make reasonable assumptions where information is missing."
}
```

### Expected Behaviour

The agent should:

- Identify missing information
- Make explicit assumptions
- Decide the document structure autonomously
- Generate an appropriate execution plan
- Produce a detailed business report
- Perform reflection/self-review
- Export a polished Microsoft Word (.docx) document

---

# Optional Stress Test

```json
{
  "request": "Prepare a detailed Standard Operating Procedure (SOP) for onboarding new software engineers in a startup. Include responsibilities, onboarding checklist, development environment setup, coding standards, Git workflow, deployment process, communication guidelines, security best practices, FAQs, and success metrics."
}
```

Expected:

- Large multi-section document
- Proper formatting
- Reflection quality check
- DOCX generation

---

# API Response Example

```json
{
  "summary": "...",
  "tasks": [
    "...",
    "..."
  ],
  "assumptions": [
    "...",
    "..."
  ],
  "document_path": "generated_docs/proposal.docx",
  "execution_log": [
    "...",
    "..."
  ]
}
```

---

# Success Criteria

✅ Planner generates task list

✅ Assumptions are identified

✅ Document sections are created

✅ Reflection/self-check completes

✅ DOCX file is generated successfully

✅ API returns structured JSON response