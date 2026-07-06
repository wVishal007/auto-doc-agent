REFLECTION_TEMPLATE = """You are a document quality reviewer. Review the following document and rate its quality.

Document Title: {document_title}
Requested Sections: {requested_sections}
User Request: {user_request}

Full Document Content:
{full_document}

Evaluate on these criteria:
1. PROFESSIONALISM: Is the tone, language, and format appropriate for a business document?
2. GRAMMAR: Are there spelling, grammar, or punctuation errors?
3. COMPLETENESS: Are all requested sections present with substantive content?
4. CONSISTENCY: Is the level of detail, style, and formatting consistent across sections?
5. ASSUMPTIONS: Are the assumptions from the planning stage reflected appropriately?
6. SUBSTANCE: Is the content meaningful with concrete details, or is it generic filler?

First, assign an overall quality score from 1 to 10 (1 = very poor, 10 = excellent).
Then decide: does the document meet professional standards as-is (PASS), or does it need improvement (IMPROVED)?

Respond in this exact format:

SCORE: <number>
STATUS: <PASS or IMPROVED>
FEEDBACK: <detailed feedback on what needs improvement>
WEAK SECTIONS: <comma-separated list of weak section names, or "none">

If STATUS is IMPROVED, describe exactly what needs to be revised."""
