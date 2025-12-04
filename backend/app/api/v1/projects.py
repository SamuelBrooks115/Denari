"""
projects.py — Project Management API Endpoints

Purpose:
- Save and retrieve project JSON data
- Projects contain user assumptions for valuation models
- Projects are stored as JSON files on the backend
"""

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Dict, Any, Optional
from pathlib import Path
import json
from datetime import datetime

from app.core.logging import get_logger

logger = get_logger(__name__)

router = APIRouter(
    prefix="/projects",
    tags=["projects"]
)

# Storage directory for project JSON files
PROJECTS_DIR = Path(__file__).parent.parent.parent.parent / "downloads" / "projects"
PROJECTS_DIR.mkdir(parents=True, exist_ok=True)


class ProjectData(BaseModel):
    """Project data model matching frontend ProjectData interface"""
    projectId: str
    createdAt: str
    updatedAt: str
    company: Dict[str, str]
    incomeStatement: Dict[str, Any]
    balanceSheet: Dict[str, Any]
    cashFlow: Dict[str, Any]
    dcf: Dict[str, Any]
    bearScenario: Optional[Dict[str, Any]] = None
    bullScenario: Optional[Dict[str, Any]] = None
    relativeValuation: Dict[str, Any]
    historicals: Optional[Dict[str, Any]] = None


class ProjectSaveResponse(BaseModel):
    """Response after saving a project"""
    success: bool
    projectId: str
    message: str


@router.post("/", response_model=ProjectSaveResponse)
async def save_project(project_data: ProjectData):
    """
    Save a project JSON to the backend.
    
    The project JSON is saved to disk and can be retrieved later for Excel export.
    """
    try:
        # Update the updatedAt timestamp
        project_data.updatedAt = datetime.utcnow().isoformat()
        
        # Save to file
        project_file = PROJECTS_DIR / f"{project_data.projectId}.json"
        with open(project_file, "w", encoding="utf-8") as f:
            json.dump(project_data.dict(), f, indent=2, ensure_ascii=False)
        
        logger.info(f"Saved project {project_data.projectId} to {project_file}")
        
        return ProjectSaveResponse(
            success=True,
            projectId=project_data.projectId,
            message="Project saved successfully"
        )
    except Exception as e:
        logger.error(f"Error saving project: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to save project: {str(e)}")


@router.get("/{project_id}", response_model=ProjectData)
async def get_project(project_id: str):
    """
    Retrieve a project JSON by project ID.
    
    Returns the project data that was previously saved.
    """
    try:
        project_file = PROJECTS_DIR / f"{project_id}.json"
        
        if not project_file.exists():
            raise HTTPException(status_code=404, detail=f"Project {project_id} not found")
        
        with open(project_file, "r", encoding="utf-8") as f:
            project_data = json.load(f)
        
        logger.info(f"Retrieved project {project_id}")
        return ProjectData(**project_data)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error retrieving project {project_id}: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to retrieve project: {str(e)}")

