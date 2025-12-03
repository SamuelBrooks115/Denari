"""
llm_classifier.py — LLM-based classification of financial line items.

This module sends fact lines to OpenAI for classification and returns
tagged FactLine objects with calc_tags populated.
"""

from __future__ import annotations

import json
from typing import Any, List

from openai import OpenAI

from app.core.config import settings
from app.core.logging import get_logger
from app.tagging.calc_tags import VALID_CALC_TAGS, get_tag_definitions
from app.tagging.llm_payload import build_classification_payload
from app.tagging.models import FactLine

logger = get_logger(__name__)


def _build_system_prompt() -> str:
    """
    Build the system prompt for LLM classification.
    
    Returns:
        System prompt string
    """
    tag_definitions = get_tag_definitions()
    
    # Build tag list by statement type
    is_tags = [
        "revenue_total", "cogs", "operating_expense", "gross_profit",
        "operating_income", "depreciation_amortization", "ebitda_adjustment_other",
        "pre_tax_income", "income_tax_expense", "net_income",
    ]
    bs_tags = [
        "ppe_net", "inventory", "accounts_payable", "accounts_receivable",
        "accrued_expenses", "total_debt_component",
    ]
    cf_tags = ["share_repurchases", "dividends_paid"]
    
    prompt = """You are a financial data classification expert. Your task is to assign zero or more calc tags from a fixed vocabulary to each line item in a financial statement.

The tags will be used later to calculate:
- Revenue, operating costs & margins, gross margin, EBITDA margin, tax rate (Income Statement)
- PP&E, inventory, accounts payable, accounts receivable, accrued expenses, total debt (Balance Sheet)
- Share repurchases, dividends as % of net income (Cash Flow Statement)

VALID TAGS:

Income Statement:
"""
    
    for tag in is_tags:
        prompt += f"- {tag}: {tag_definitions[tag]}\n"
    
    prompt += "\nBalance Sheet:\n"
    for tag in bs_tags:
        prompt += f"- {tag}: {tag_definitions[tag]}\n"
    
    prompt += "\nCash Flow:\n"
    for tag in cf_tags:
        prompt += f"- {tag}: {tag_definitions[tag]}\n"
    
    prompt += """
RULES:
1. Do NOT invent new tags. Only use tags from the list above.
2. If no tag applies to a line item, return an empty list for that line.
3. Prefer GAAP totals over subcomponents when choosing *_total tags.
4. Avoid non-GAAP "Adjusted" lines unless explicitly labeled as GAAP.
5. Abstract concepts (is_abstract: true) typically should not be tagged unless they represent a meaningful total.
6. Consider the parent_label and label together to understand hierarchy.
7. value_hint is provided for context (scale, sign) but should not be the primary classification signal.

Return a JSON object with this structure:
{
  "tags": [
    { "line_id": "IS__Revenue__Consolidated", "calc_tags": ["revenue_total"] },
    { "line_id": "IS__CostOfSales__Consolidated", "calc_tags": ["cogs"] }
  ]
}

Each entry in "tags" must have:
- line_id: exactly matching one of the input line_ids
- calc_tags: array of zero or more valid tag strings
"""
    
    return prompt


def _build_user_prompt(statement_type: str, payload: dict[str, Any]) -> str:
    """
    Build the user prompt with statement type and lines payload.
    
    Args:
        statement_type: "IS", "BS", or "CF"
        payload: Classification payload from build_classification_payload()
        
    Returns:
        User prompt string
    """
    statement_name = {
        "IS": "Income Statement",
        "BS": "Balance Sheet",
        "CF": "Cash Flow Statement",
    }.get(statement_type, statement_type)
    
    prompt = f"""Classify the following line items from a {statement_name}:

{json.dumps(payload, indent=2)}

Return JSON with the "tags" array mapping each line_id to its calc_tags."""
    
    return prompt


def classify_fact_lines_with_llm(
    lines: List[FactLine],
    statement_type: str,
) -> List[FactLine]:
    """
    Call the OpenAI Chat Completions API to classify the given lines for a single statement type.
    
    Args:
        lines: List of FactLine objects to classify
        statement_type: "IS", "BS", or "CF"
        
    Returns:
        New FactLine objects with calc_tags populated
        
    Raises:
        ValueError: If API key is missing or response is invalid
        RuntimeError: If API call fails
    """
    if not lines:
        logger.warning(f"No lines provided for {statement_type} classification")
        return []
    
    # Check API key
    if not settings.OPENAI_API_KEY or not settings.OPENAI_API_KEY.strip():
        raise ValueError(
            "OpenAI API key not configured. Set OPENAI_API_KEY environment variable "
            "or configure in settings."
        )
    
    # Build payload
    payload = build_classification_payload(statement_type, lines)
    
    # Build prompts
    system_prompt = _build_system_prompt()
    user_prompt = _build_user_prompt(statement_type, payload)
    
    # Initialize OpenAI client
    client = OpenAI(api_key=settings.OPENAI_API_KEY, timeout=60)
    
    logger.info(f"Classifying {len(lines)} {statement_type} lines with OpenAI")
    
    try:
        response = client.chat.completions.create(
            model=settings.OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.1,  # Low temperature for consistent classification
            response_format={"type": "json_object"},
        )
        
        content = response.choices[0].message.content
        if not content:
            raise ValueError("Empty response from LLM")
        
        # Parse JSON response
        result = json.loads(content)
        
        # Validate response structure
        if "tags" not in result:
            raise ValueError("LLM response missing 'tags' field")
        
        if not isinstance(result["tags"], list):
            raise ValueError("LLM response 'tags' must be a list")
        
        # Build mapping from line_id to calc_tags
        line_id_to_tags: dict[str, list[str]] = {}
        input_line_ids = {line.line_id for line in lines}
        
        for tag_entry in result["tags"]:
            if not isinstance(tag_entry, dict):
                logger.warning(f"Invalid tag entry (not a dict): {tag_entry}")
                continue
            
            line_id = tag_entry.get("line_id")
            calc_tags = tag_entry.get("calc_tags", [])
            
            if not line_id:
                logger.warning(f"Tag entry missing line_id: {tag_entry}")
                continue
            
            # Validate line_id exists in input
            if line_id not in input_line_ids:
                logger.warning(f"LLM returned line_id not in input: {line_id}")
                continue
            
            # Validate calc_tags
            if not isinstance(calc_tags, list):
                logger.warning(f"calc_tags for {line_id} is not a list: {calc_tags}")
                calc_tags = []
            
            # Filter to only valid tags
            valid_tags = [tag for tag in calc_tags if tag in VALID_CALC_TAGS]
            invalid_tags = [tag for tag in calc_tags if tag not in VALID_CALC_TAGS]
            
            if invalid_tags:
                logger.warning(
                    f"Invalid calc_tags for {line_id}: {invalid_tags}. "
                    f"Valid tags: {sorted(VALID_CALC_TAGS)}"
                )
            
            line_id_to_tags[line_id] = valid_tags
        
        # Merge tags back into FactLine objects
        tagged_lines = []
        for line in lines:
            # Create new FactLine with calc_tags populated
            tagged_line = FactLine(
                line_id=line.line_id,
                statement_type=line.statement_type,
                role_uri=line.role_uri,
                label=line.label,
                parent_label=line.parent_label,
                concept_qname=line.concept_qname,
                is_abstract=line.is_abstract,
                period_start=line.period_start,
                period_end=line.period_end,
                value=line.value,
                unit=line.unit,
                dimensions=line.dimensions,
                calc_tags=line_id_to_tags.get(line.line_id, []),
            )
            tagged_lines.append(tagged_line)
        
        # Log summary
        total_tagged = sum(1 for line in tagged_lines if line.calc_tags)
        logger.info(
            f"Classification complete: {total_tagged}/{len(tagged_lines)} lines tagged "
            f"for {statement_type}"
        )
        
        return tagged_lines
    
    except json.JSONDecodeError as e:
        raise ValueError(f"Failed to parse LLM JSON response: {e}")
    
    except Exception as e:
        raise RuntimeError(f"OpenAI API call failed: {e}") from e

