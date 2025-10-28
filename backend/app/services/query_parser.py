"""
Query Parser Service - Uses Gemini to classify and extract query intent

Determines if a user's question is:
- temporal: Time-based queries (last N commits, recent, yesterday)
- semantic: Meaning-based queries (authentication fixes, bug changes)
- hybrid: Both temporal filters + semantic search
"""

import logging
import json
from typing import Dict, Optional, List
from app.services.gemini_service import call_gemini

logger = logging.getLogger(__name__)


def parse_query(question: str) -> Dict:
    """
    Parse user query using Gemini to extract intent and filters
    
    Args:
        question: User's natural language question
        
    Returns:
        Dictionary with:
        - query_type: "temporal", "semantic", or "hybrid"
        - temporal: {type, value, limit} or None
        - author: author name filter or None
        - files: list of file patterns or None
        - semantic_query: cleaned semantic search text or None
        
    Examples:
        "last 5 commits" → {query_type: "temporal", temporal: {limit: 5}}
        "authentication bugs" → {query_type: "semantic", semantic_query: "authentication bugs"}
        "auth changes last week" → {query_type: "hybrid", temporal: {...}, semantic_query: "auth changes"}
    """
    
    prompt = f"""You are a query parser for a commit history search system. Analyze the user's question and extract structured information.

User Question: "{question}"

Classify the query type and extract filters. Return ONLY valid JSON with this exact structure:

{{
  "query_type": "temporal" | "semantic" | "hybrid",
  "temporal": {{
    "type": "limit" | "days" | "weeks" | "months" | "date_range",
    "value": number or string,
    "direction": "past" | "future"
  }} or null,
  "author": "author name" or null,
  "files": ["file1.py", "file2.js"] or null,
  "semantic_query": "cleaned semantic search text" or null
}}

Classification Rules:
- "temporal": Time/count/author/file filters WITHOUT semantic search (last N, by author, recent, yesterday)
  → Questions like "what", "why", "show me" with temporal filters are STILL temporal
  → Just return the filtered commits, don't search by meaning
- "semantic": ONLY meaning-based search when there's NO temporal filter (bug fixes, authentication, how did we)
  → Search by concepts, keywords, topics
- "hybrid": BOTH temporal filters AND specific semantic keywords that need similarity search
  → Example: "authentication changes last week" (need to search for "authentication" within last week)

IMPORTANT: Questions starting with "what/why/show me" followed by "last N commits" are TEMPORAL, not hybrid!
The user just wants to see those N commits, not search semantically.

Examples:
Q: "last 5 commits" → {{"query_type": "temporal", "temporal": {{"type": "limit", "value": 5, "direction": "past"}}, "author": null, "files": null, "semantic_query": null}}
Q: "what was done in the last 2 commits" → {{"query_type": "temporal", "temporal": {{"type": "limit", "value": 2, "direction": "past"}}, "author": null, "files": null, "semantic_query": null}}
Q: "show me recent commits" → {{"query_type": "temporal", "temporal": {{"type": "limit", "value": 10, "direction": "past"}}, "author": null, "files": null, "semantic_query": null}}
Q: "authentication bug fixes" → {{"query_type": "semantic", "temporal": null, "author": null, "files": null, "semantic_query": "authentication bug fixes"}}
Q: "how did we handle authentication" → {{"query_type": "semantic", "temporal": null, "author": null, "files": null, "semantic_query": "how did we handle authentication"}}
Q: "authentication changes from last week" → {{"query_type": "hybrid", "temporal": {{"type": "days", "value": 7, "direction": "past"}}, "author": null, "files": null, "semantic_query": "authentication changes"}}
Q: "commits by John" → {{"query_type": "temporal", "temporal": null, "author": "John", "files": null, "semantic_query": null}}
Q: "what did John commit yesterday" → {{"query_type": "temporal", "temporal": {{"type": "days", "value": 1, "direction": "past"}}, "author": "John", "files": null, "semantic_query": null}}
Q: "John's authentication changes yesterday" → {{"query_type": "hybrid", "temporal": {{"type": "days", "value": 1, "direction": "past"}}, "author": "John", "files": null, "semantic_query": "authentication changes"}}

Now parse this question and return ONLY the JSON:
"""

    try:
        response = call_gemini(prompt)
        
        # Clean response - remove markdown code blocks if present
        response = response.strip()
        if response.startswith("```json"):
            response = response[7:]
        if response.startswith("```"):
            response = response[3:]
        if response.endswith("```"):
            response = response[:-3]
        response = response.strip()
        
        # Parse JSON
        parsed = json.loads(response)
        
        # Validate required fields
        if "query_type" not in parsed:
            raise ValueError("Missing query_type in response")
        
        if parsed["query_type"] not in ["temporal", "semantic", "hybrid"]:
            raise ValueError(f"Invalid query_type: {parsed['query_type']}")
        
        logger.info(f"✅ Parsed query: {parsed['query_type']} - {question[:50]}")
        return parsed
        
    except json.JSONDecodeError as e:
        logger.error(f"❌ Failed to parse Gemini response as JSON: {e}")
        logger.error(f"Response was: {response[:200]}")
        # Fallback to semantic search
        return {
            "query_type": "semantic",
            "temporal": None,
            "author": None,
            "files": None,
            "semantic_query": question
        }
    except Exception as e:
        logger.error(f"❌ Query parsing error: {e}")
        # Fallback to semantic search
        return {
            "query_type": "semantic",
            "temporal": None,
            "author": None,
            "files": None,
            "semantic_query": question
        }


def build_temporal_sql_filters(parsed: Dict) -> tuple[str, list]:
    """
    Build SQL WHERE clause and parameters from parsed query
    
    Returns:
        (where_clause, params) tuple
    """
    
    conditions = []
    params = []
    
    # Temporal filter
    if parsed.get("temporal"):
        temporal = parsed["temporal"]
        
        if temporal["type"] == "limit":
            # Handled by LIMIT clause, not WHERE
            pass
        elif temporal["type"] == "days":
            days = temporal["value"]
            conditions.append("commit_date >= DATEADD(day, -%s, CURRENT_TIMESTAMP())")
            params.append(days)
        elif temporal["type"] == "weeks":
            weeks = temporal["value"]
            conditions.append("commit_date >= DATEADD(week, -%s, CURRENT_TIMESTAMP())")
            params.append(weeks)
        elif temporal["type"] == "months":
            months = temporal["value"]
            conditions.append("commit_date >= DATEADD(month, -%s, CURRENT_TIMESTAMP())")
            params.append(months)
    
    # Author filter
    if parsed.get("author"):
        conditions.append("(author_name ILIKE %s OR author_email ILIKE %s)")
        author_pattern = f"%{parsed['author']}%"
        params.append(author_pattern)
        params.append(author_pattern)
    
    # File filter
    if parsed.get("files") and len(parsed["files"]) > 0:
        file_conditions = []
        for file in parsed["files"]:
            file_conditions.append("ARRAY_CONTAINS(%s::VARIANT, files_changed)")
            params.append(file)
        conditions.append(f"({' OR '.join(file_conditions)})")
    
    where_clause = " AND ".join(conditions) if conditions else ""
    return where_clause, params


def get_temporal_limit(parsed: Dict) -> Optional[int]:
    """Extract LIMIT value from temporal filter"""
    if parsed.get("temporal") and parsed["temporal"].get("type") == "limit":
        return parsed["temporal"]["value"]
    return None
