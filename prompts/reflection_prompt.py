REFLECTION_TEMPLATE = """You are a document quality reviewer. Review the following document content and check for completeness and quality.

Document Title: {document_title}
Requested Sections: {requested_sections}

Generated Content:
{generated_content}

Check for:
1. Are all requested sections present with substantive content?
2. Is the writing professional, clear, and business-appropriate?
3. Is the content complete or are there gaps?
4. Does it meet the quality expected for a business document?

If everything is complete and well-written, respond with exactly: PASS

If something important is missing or poorly written, respond with exactly: IMPROVED
Then list what needs to be added or improved.

Review Result:"""
