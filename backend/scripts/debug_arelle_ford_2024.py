"""
debug_arelle_ford_2024.py — Debug script to verify Arelle is working with Ford 2024 10-K.

This script:
1. Loads the Ford 2024 10-K iXBRL file
2. Prints available role URIs
3. Prints raw facts inspection
4. Prints sample facts for basic GAAP tags using local-name search

Usage:
    python scripts/debug_arelle_ford_2024.py --xbrl-file data/xbrl/ford_2024_10k.ixbrl [--dump-json]
"""

from __future__ import annotations

import argparse
import json
import sys
from datetime import timedelta
from pathlib import Path

from app.xbrl.arelle_loader import (
    find_role_by_keywords,
    get_role_uris,
    load_xbrl_instance,
)
from app.xbrl.debt_note_extractor import classify_segment_from_dimensions


def extract_fact_summary(fact, model_xbrl):
    """Extract summary info from a fact for debugging."""
    # Get QName (try multiple methods)
    qname_str = None
    if hasattr(fact, "qname") and fact.qname:
        qname_str = str(fact.qname)
    elif hasattr(fact, "elementQname") and fact.elementQname:
        qname_str = str(fact.elementQname)
    elif hasattr(fact, "concept") and fact.concept and hasattr(fact.concept, "qname"):
        qname_str = str(fact.concept.qname)
    
    local_name = qname_str.split(":")[-1] if qname_str and ":" in qname_str else qname_str
    
    # Get value (textValue first for iXBRL)
    value = None
    if hasattr(fact, "textValue") and fact.textValue:
        try:
            value = float(str(fact.textValue).replace(",", "").strip())
        except (ValueError, TypeError):
            pass
    elif hasattr(fact, "xValue") and fact.xValue is not None:
        value = fact.xValue
    
    # Get period
    period_end = None
    if fact.context is not None:
        if hasattr(fact.context, "endDatetime") and fact.context.endDatetime is not None:
            period_end = (fact.context.endDatetime.date() - timedelta(days=1)).isoformat()
        elif hasattr(fact.context, "instantDatetime") and fact.context.instantDatetime is not None:
            period_end = fact.context.instantDatetime.date().isoformat()
    
    # Get segment classification using the existing function
    segment = classify_segment_from_dimensions(fact.context)
    
    # Also get raw dimension strings for debugging
    raw_dimensions = []
    if fact.context is not None and hasattr(fact.context, "segDimValues") and fact.context.segDimValues is not None:
        for dim in fact.context.segDimValues:
            raw_dimensions.append(str(dim))
    
    return {
        "qname": qname_str,
        "local_name": local_name,
        "value": value,
        "period_end": period_end,
        "segment": segment,  # Classified segment: "consolidated", "company_excl_ford_credit", "ford_credit", "other"
        "raw_dimensions": raw_dimensions,  # Raw dimension strings for debugging
        "context_id": fact.contextID if hasattr(fact, "contextID") else None,
    }


def find_facts_by_localname(model_xbrl, localname: str, target_year: int, max_results: int = 10):
    """Find facts by local name and fiscal year."""
    matches = []
    for fact in model_xbrl.facts:
        # Get local name
        fact_local = None
        if hasattr(fact, "qname") and fact.qname:
            fact_qname_str = str(fact.qname)
            fact_local = fact_qname_str.split(":")[-1] if ":" in fact_qname_str else fact_qname_str
        elif hasattr(fact, "elementQname") and fact.elementQname:
            fact_qname_str = str(fact.elementQname)
            fact_local = fact_qname_str.split(":")[-1] if ":" in fact_qname_str else fact_qname_str
        elif hasattr(fact, "concept") and fact.concept and hasattr(fact.concept, "qname"):
            fact_qname_str = str(fact.concept.qname)
            fact_local = fact_qname_str.split(":")[-1] if ":" in fact_qname_str else fact_qname_str
        
        if fact_local != localname:
            continue
        
        # Check period
        period_end = None
        if fact.context is not None:
            if hasattr(fact.context, "endDatetime") and fact.context.endDatetime is not None:
                period_end = (fact.context.endDatetime.date() - timedelta(days=1)).isoformat()
            elif hasattr(fact.context, "instantDatetime") and fact.context.instantDatetime is not None:
                period_end = fact.context.instantDatetime.date().isoformat()
        
        if not period_end:
            continue
        
        try:
            period_year = int(period_end.split("-")[0])
            if period_year != target_year:
                continue
        except (ValueError, TypeError):
            continue
        
        # Get value
        value = None
        if hasattr(fact, "textValue") and fact.textValue:
            try:
                value = float(str(fact.textValue).replace(",", "").strip())
            except (ValueError, TypeError):
                pass
        elif hasattr(fact, "xValue") and fact.xValue is not None:
            value = fact.xValue
        
        if value is not None:
            matches.append((fact, period_end, value))
    
    return matches[:max_results]


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Debug Arelle loading for Ford 2024 10-K"
    )
    parser.add_argument(
        "--xbrl-file",
        type=str,
        default="data/xbrl/ford_2024_10k.ixbrl",
        help="Path to Ford 2024 10-K iXBRL file (default: data/xbrl/ford_2024_10k.ixbrl)",
    )
    parser.add_argument(
        "--log-file",
        type=str,
        default="arelle.log",
        help="Path to Arelle log file (default: arelle.log)",
    )
    parser.add_argument(
        "--dump-json",
        action="store_true",
        help="Dump raw facts to JSON file (outputs/F_FY2024_arelle_raw_facts_debug.json)",
    )
    parser.add_argument(
        "--fiscal-year",
        type=int,
        default=2024,
        help="Target fiscal year for fact filtering (default: 2024)",
    )
    
    args = parser.parse_args()
    
    try:
        # Load XBRL instance
        print(f"Loading XBRL instance from: {args.xbrl_file}")
        model_xbrl = load_xbrl_instance(args.xbrl_file, log_file=args.log_file)
        
        # Print basic stats
        print("\n" + "=" * 80)
        print("XBRL Instance Statistics")
        print("=" * 80)
        print(f"Total facts: {len(model_xbrl.facts)}")
        print(f"Total contexts: {len(model_xbrl.contexts)}")
        
        # Get role types count with fallback
        role_types = getattr(model_xbrl, "modelRoleTypes", None)
        if role_types is None:
            role_types = getattr(model_xbrl, "roleTypes", {})
        
        if not isinstance(role_types, dict):
            if hasattr(role_types, "values"):
                role_types = {k: v for k, v in enumerate(role_types.values())} if hasattr(role_types, "__iter__") else {}
            else:
                role_types = {}
        
        role_count = len(role_types) if isinstance(role_types, dict) else 0
        print(f"Total role types: {role_count}")
        if role_count == 0:
            print("  Warning: No role types found. This may be normal for some XBRL instances.")
        
        print(f"Total units: {len(model_xbrl.units)}")
        
        # Print role URIs
        print("\n" + "=" * 80)
        print("Available Role URIs (first 20)")
        print("=" * 80)
        roles = get_role_uris(model_xbrl)
        for i, (role_uri, definition) in enumerate(list(roles.items())[:20]):
            print(f"{i+1}. {role_uri}")
            if definition:
                print(f"   Definition: {definition[:100]}...")
            print()
        
        # Search for debt-related roles
        print("\n" + "=" * 80)
        print("Searching for Debt-related Roles")
        print("=" * 80)
        debt_role = find_role_by_keywords(model_xbrl, ["debt", "commitments"])
        if debt_role:
            print(f"Found debt role: {debt_role}")
        else:
            print("No debt role found with keywords ['debt', 'commitments']")
        
        # Print first N facts (raw inspection)
        print("\n" + "=" * 80)
        print("First 30 Facts (Raw Inspection)")
        print("=" * 80)
        facts_shown = 0
        for i, fact in enumerate(list(model_xbrl.facts)[:30]):
            summary = extract_fact_summary(fact, model_xbrl)
            if summary["qname"]:  # Only show facts with QNames
                facts_shown += 1
                print(f"{facts_shown}. {summary['qname']} (local: {summary['local_name']})")
                print(f"   Value: {summary['value']}")
                print(f"   Period: {summary['period_end']}")
                print(f"   Segment: {summary['segment']}")
                if summary.get('raw_dimensions'):
                    print(f"   Dimensions: {' | '.join(summary['raw_dimensions'])}")
                print(f"   Context: {summary['context_id']}")
                print()
        
        # Print sample facts for common GAAP tags (local-name search)
        print("\n" + "=" * 80)
        print("Sample Facts for Common GAAP Tags (Local-Name Search)")
        print("=" * 80)
        
        fiscal_year = args.fiscal_year
        
        core_tags = {
            "Assets": ["Assets"],
            "Liabilities": ["Liabilities"],
            "StockholdersEquity": ["StockholdersEquity"],
            "Revenues": ["Revenues"],
            "NetIncomeLoss": ["NetIncomeLoss"],
            "CashAndCashEquivalentsAtCarryingValue": ["CashAndCashEquivalentsAtCarryingValue"],
        }
        
        # Add fallback variants
        fallback_tags = {
            "Assets": ["AssetsCurrent", "AssetsNoncurrent"],
            "Liabilities": ["LiabilitiesCurrent", "LiabilitiesNoncurrent"],
            "StockholdersEquity": ["StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest", "Equity"],
        }
        
        found_any = False
        
        for tag_group, localnames in core_tags.items():
            print(f"\n{tag_group}:")
            matches = []
            for localname in localnames:
                matches.extend(find_facts_by_localname(model_xbrl, localname, fiscal_year))
            
            if not matches and tag_group in fallback_tags:
                # Try fallbacks
                for fallback_name in fallback_tags[tag_group]:
                    matches.extend(find_facts_by_localname(model_xbrl, fallback_name, fiscal_year))
            
            if matches:
                found_any = True
                for fact, period, value in matches[:5]:  # Show first 5
                    qname = str(fact.qname) if hasattr(fact, "qname") and fact.qname else "unknown"
                    context_id = fact.contextID if hasattr(fact, "contextID") else "N/A"
                    print(f"  - {qname}: {value:,.0f} (period: {period}, context: {context_id})")
            else:
                print(f"  No facts found")
        
        # Fail loudly if no core facts found
        if not found_any:
            print("\n" + "!" * 80)
            print("ERROR: No core GAAP-like facts (Assets / Liabilities / NetIncomeLoss) were found")
            print("using local-name search. Check taxonomy version and raw facts above.")
            print("!" * 80)
            sys.exit(1)
        
        # Optional JSON dump
        if args.dump_json:
            print("\n" + "=" * 80)
            print("Dumping Raw Facts to JSON")
            print("=" * 80)
            
            # Get entity info
            entity_name = "Unknown"
            cik = "Unknown"
            if hasattr(model_xbrl, "facts") and model_xbrl.facts:
                # Try to find entity name from facts
                for fact in list(model_xbrl.facts)[:100]:
                    if hasattr(fact, "concept") and fact.concept:
                        concept_qname = str(fact.concept.qname) if hasattr(fact.concept, "qname") else ""
                        if "EntityRegistrantName" in concept_qname or "EntityCentralIndexKey" in concept_qname:
                            if hasattr(fact, "textValue") and fact.textValue:
                                if "EntityRegistrantName" in concept_qname:
                                    entity_name = str(fact.textValue)
                                elif "EntityCentralIndexKey" in concept_qname:
                                    cik = str(fact.textValue)
            
            # Collect all facts
            facts_data = []
            for fact in model_xbrl.facts:
                summary = extract_fact_summary(fact, model_xbrl)
                if summary["qname"] and summary["value"] is not None:
                    # Get unit
                    unit = "USD"
                    if hasattr(fact, "unitID") and fact.unitID and hasattr(model_xbrl, "units"):
                        unit_obj = model_xbrl.units.get(fact.unitID)
                        if unit_obj is not None and hasattr(unit_obj, "measures"):
                            measures = unit_obj.measures
                            if measures and len(measures) > 0:
                                unit = str(measures[0][0]) if isinstance(measures[0], tuple) else str(measures[0])
                    
                    # Get namespace
                    namespace = ""
                    if summary["qname"] and ":" in summary["qname"]:
                        prefix = summary["qname"].split(":")[0]
                        # Try multiple ways to get namespace
                        if hasattr(model_xbrl, "qnameNamespaces") and model_xbrl.qnameNamespaces:
                            namespace = model_xbrl.qnameNamespaces.get(prefix, "")
                        elif hasattr(fact, "concept") and fact.concept:
                            # Try to get namespace from concept
                            if hasattr(fact.concept, "namespaceURI"):
                                namespace = fact.concept.namespaceURI
                            elif hasattr(fact.concept, "qname") and fact.concept.qname:
                                # Extract namespace from QName if available
                                qname_obj = fact.concept.qname
                                if hasattr(qname_obj, "namespaceURI"):
                                    namespace = qname_obj.namespaceURI
                    
                    facts_data.append({
                        "concept_qname": summary["qname"],
                        "local_name": summary["local_name"],
                        "namespace": namespace,
                        "value": summary["value"],
                        "unit": unit,
                        "end": summary["period_end"],
                        "segment": summary["segment"],  # Classified segment
                        "raw_dimensions": summary.get("raw_dimensions", []),  # Raw dimensions for debugging
                        "context_id": summary["context_id"],
                    })
            
            # Write JSON
            output_dir = Path("outputs")
            output_dir.mkdir(exist_ok=True)
            output_file = output_dir / "F_FY2024_arelle_raw_facts_debug.json"
            
            dump_data = {
                "company": entity_name,
                "cik": cik,
                "fiscal_year": fiscal_year,
                "facts": facts_data,
            }
            
            with open(output_file, "w", encoding="utf-8") as f:
                json.dump(dump_data, f, indent=2, ensure_ascii=False)
            
            print(f"  Dumped {len(facts_data)} facts to: {output_file}")
        
        print("\n" + "=" * 80)
        print("Debug complete!")
        print("=" * 80)
    
    except ImportError as e:
        print(f"\nError: {e}")
        print("\nInstall Arelle with:")
        print("  pip install arelle-release")
        print("  or")
        print("  poetry add arelle-release")
    
    except FileNotFoundError as e:
        print(f"\nError: {e}")
        print("\nPlease provide a valid XBRL file path.")
        print("You can download Ford's 2024 10-K iXBRL from SEC EDGAR.")
    
    except Exception as e:
        print(f"\nError: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()

