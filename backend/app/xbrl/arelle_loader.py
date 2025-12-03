"""
arelle_loader.py — Arelle-based XBRL instance loader.

DEPRECATED — This module has been replaced by the FMP-based pipeline.
See app/data/fmp_client.py for the new implementation.

This module provides a clean interface to load and work with XBRL instances using Arelle.
It abstracts away Arelle-specific details and provides a simple API for loading XBRL files.

Uses Arelle Python API to:
- Load inline XBRL (iXBRL) or standard XBRL instance documents
- Provide access to model_xbrl for querying facts, contexts, dimensions, roles, etc.
- Handle Arelle initialization and configuration

Expected usage:
    from app.xbrl.arelle_loader import load_xbrl_instance
    
    model_xbrl = load_xbrl_instance("data/xbrl/ford_2024_10k.ixbrl")
    # Use model_xbrl to extract facts, contexts, etc.
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional

from app.core.logging import get_logger

logger = get_logger(__name__)

# Try to import Arelle - will raise ImportError if not installed
try:
    from arelle import Cntlr
    from arelle.ModelManager import ModelManager
    ARELLE_AVAILABLE = True
except ImportError:
    ARELLE_AVAILABLE = False
    logger.warning(
        "Arelle not available. Install with: pip install arelle-release "
        "or poetry add arelle-release"
    )


def load_xbrl_instance(
    file_path: str | Path,
    log_file: Optional[str | Path] = None,
) -> "ModelXbrl":
    """
    Load an XBRL instance document using Arelle.
    
    Supports:
    - Inline XBRL (.ixbrl, .html)
    - Standard XBRL (.xbrl, .xml)
    - ZIP archives containing XBRL instances
    
    Args:
        file_path: Path to XBRL instance file (relative to repo root or absolute)
        log_file: Optional path for Arelle log file (default: arelle.log in current dir)
        
    Returns:
        Arelle ModelXbrl object that can be queried for facts, contexts, roles, etc.
        
    Raises:
        ImportError: If Arelle is not installed
        FileNotFoundError: If the XBRL file doesn't exist
        RuntimeError: If Arelle fails to load the instance
        
    Example:
        >>> model_xbrl = load_xbrl_instance("data/xbrl/ford_2024_10k.ixbrl")
        >>> # Access facts
        >>> for fact in model_xbrl.facts:
        ...     print(f"{fact.concept.qname}: {fact.xValue}")
    """
    if not ARELLE_AVAILABLE:
        raise ImportError(
            "Arelle is not installed. Install with: pip install arelle-release"
        )
    
    # Resolve file path
    file_path = Path(file_path)
    if not file_path.is_absolute():
        # Try relative to repo root
        repo_root = Path(__file__).parent.parent.parent
        file_path = repo_root / file_path
    
    if not file_path.exists():
        raise FileNotFoundError(f"XBRL file not found: {file_path}")
    
    logger.info(f"Loading XBRL instance from: {file_path}")
    
    # Initialize Arelle controller
    # Use a minimal controller for loading (no GUI, no web server)
    cntlr = Cntlr.Cntlr()
    
    # Set log file if provided
    if log_file:
        log_path = Path(log_file)
        if not log_path.is_absolute():
            log_path = Path.cwd() / log_path
        cntlr.logFileName = str(log_path)
    
    # Load the XBRL instance
    try:
        model_xbrl = cntlr.modelManager.load(str(file_path))
        
        if model_xbrl is None:
            raise RuntimeError(f"Arelle failed to load XBRL instance: {file_path}")
        
        # Get role types count with fallback
        role_types = getattr(model_xbrl, "modelRoleTypes", None)
        if role_types is None:
            role_types = getattr(model_xbrl, "roleTypes", {})
        role_count = len(role_types) if isinstance(role_types, dict) else 0
        
        logger.info(
            f"Successfully loaded XBRL instance: "
            f"{len(model_xbrl.facts)} facts, "
            f"{len(model_xbrl.contexts)} contexts, "
            f"{role_count} role types"
        )
        
        return model_xbrl
    
    except Exception as e:
        logger.error(f"Error loading XBRL instance {file_path}: {e}")
        raise RuntimeError(f"Failed to load XBRL instance: {e}") from e


def get_role_uris(model_xbrl: "ModelXbrl") -> dict[str, str]:
    """
    Get all role URIs and their definitions from the XBRL instance.
    
    Useful for finding specific disclosure roles (e.g., Note 18 - Debt and Commitments).
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        
    Returns:
        Dictionary mapping role URI -> role definition/description
    """
    roles = {}
    
    # Try multiple attribute names for role types
    role_types = getattr(model_xbrl, "modelRoleTypes", None)
    if role_types is None:
        role_types = getattr(model_xbrl, "roleTypes", {})
    
    # Handle if it's not a dict
    if not isinstance(role_types, dict):
        if hasattr(role_types, "values"):
            # Convert to dict if it's iterable
            if hasattr(role_types, "__iter__"):
                role_types = {k: v for k, v in enumerate(role_types.values())} if hasattr(role_types, "values") else {}
            else:
                role_types = {}
        else:
            role_types = {}
    
    # Extract role URIs
    for role_type in role_types.values():
        if hasattr(role_type, "roleURI"):
            role_uri = role_type.roleURI
            definition = getattr(role_type, "definition", None) or getattr(role_type, "usedOn", None) or ""
            roles[role_uri] = definition
    
    return roles


def find_role_by_keywords(
    model_xbrl: "ModelXbrl",
    keywords: list[str],
) -> Optional[str]:
    """
    Find a role URI by searching role definitions for keywords.
    
    Useful for finding specific notes/disclosures (e.g., "Debt", "Commitments").
    
    Args:
        model_xbrl: Arelle ModelXbrl object
        keywords: List of keywords to search for (case-insensitive)
        
    Returns:
        Role URI if found, None otherwise
    """
    roles = get_role_uris(model_xbrl)
    
    keywords_lower = [kw.lower() for kw in keywords]
    
    for role_uri, definition in roles.items():
        definition_lower = definition.lower()
        if all(kw in definition_lower for kw in keywords_lower):
            logger.info(f"Found role matching keywords {keywords}: {role_uri}")
            return role_uri
    
    return None

