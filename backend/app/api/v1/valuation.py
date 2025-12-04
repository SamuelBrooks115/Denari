"""
valuation.py — Valuation Export API Endpoints

Purpose:
- Export Excel files from saved project JSON
- Uses existing Excel export functions without modifying them
"""

from fastapi import APIRouter, HTTPException
from fastapi.responses import FileResponse
from pydantic import BaseModel
from pathlib import Path
import json

from app.core.logging import get_logger
from app.api.v1.projects import PROJECTS_DIR
from app.services.modeling.excel_export import populate_template_from_json

logger = get_logger(__name__)

router = APIRouter(
    prefix="/valuation",
    tags=["valuation"]
)

# Paths for templates and outputs
DOWNLOADS_DIR = Path(__file__).parent.parent.parent.parent / "downloads"
TEMPLATE_PATH = DOWNLOADS_DIR / "Denari_Final_v2.xlsx"


class ExportRequest(BaseModel):
    """Request to export Excel file"""
    projectId: str


@router.post("/export")
async def export_valuation(request: ExportRequest):
    """
    Export Excel file for a project.
    
    This endpoint:
    1. Loads the project JSON from disk
    2. Fetches FMP data for the company (if needed)
    3. Calls populate_template_from_json with the project JSON as assumptions
    4. Returns the Excel file for download
    
    The project JSON must be saved first via POST /api/v1/projects/
    """
    try:
        # Step 1: Load project JSON
        project_file = PROJECTS_DIR / f"{request.projectId}.json"
        if not project_file.exists():
            raise HTTPException(status_code=404, detail=f"Project {request.projectId} not found. Please save the project first.")
        
        logger.info(f"Loading project {request.projectId} from {project_file}")
        with open(project_file, "r", encoding="utf-8") as f:
            project_data = json.load(f)
        
        ticker = project_data.get("company", {}).get("ticker", "").upper()
        if not ticker:
            raise HTTPException(status_code=400, detail="Project missing company ticker")
        
        # Step 2: Check if template exists
        if not TEMPLATE_PATH.exists():
            raise HTTPException(
                status_code=500,
                detail=f"Excel template not found at {TEMPLATE_PATH}. Please ensure the template is available."
            )
        
        # Step 3: Check if FMP combined JSON exists (required for populate_template_from_json)
        # The FMP JSON should be created by the frontend or ingestion process
        # For now, we'll look for it in the downloads directory
        fmp_json_pattern = f"*{ticker}*combined_fmp.json"
        fmp_json_files = list(DOWNLOADS_DIR.glob(fmp_json_pattern))
        
        if not fmp_json_files:
            # Try alternative pattern
            fmp_json_pattern = f"{ticker}_combined_fmp.json"
            fmp_json_path = DOWNLOADS_DIR / fmp_json_pattern
            if not fmp_json_path.exists():
                raise HTTPException(
                    status_code=404,
                    detail=f"FMP combined JSON not found for {ticker}. Please ensure financial data has been fetched."
                )
            fmp_json_path_str = str(fmp_json_path)
        else:
            # Use the most recent FMP JSON file
            fmp_json_path_str = str(max(fmp_json_files, key=lambda p: p.stat().st_mtime))
        
        logger.info(f"Using FMP JSON: {fmp_json_path_str}")
        
        # Step 4: Create temporary output file in downloads directory
        # Use downloads directory so it's easier to find and debug if needed
        output_dir = DOWNLOADS_DIR / "exports"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Generate a friendly filename
        company_name = project_data.get("company", {}).get("name", ticker)
        safe_company_name = "".join(c for c in company_name if c.isalnum() or c in (' ', '-', '_')).strip()
        filename = f"{safe_company_name}_{ticker}_valuation.xlsx"
        output_path = output_dir / filename
        
        logger.info(f"Exporting Excel to {output_path}")
        
        # Step 5: Call populate_template_from_json with assumptions_path
        # This function will:
        # - Load the FMP JSON for historical financial data
        # - Load the project JSON (assumptions_path) for user assumptions
        # - Populate the Excel template
        populate_template_from_json(
            json_path=fmp_json_path_str,
            template_path=str(TEMPLATE_PATH),
            output_path=str(output_path),
            target_sheets=["DCF Base", "DCF Bear", "DCF Bull", "3 Statement"],
            assumptions_path=str(project_file)
        )
        
        logger.info(f"Excel export complete: {output_path}")
        
        # Step 6: Return file for download
        return FileResponse(
            path=str(output_path),
            filename=filename,
            media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting valuation for project {request.projectId}: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Failed to export valuation: {str(e)}")

