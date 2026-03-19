from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from gamevcs.server.database import get_db
from gamevcs.server.models import (
    User,
    Project,
    ProjectCreate,
    ProjectResponse,
    Branch,
    BranchCreate,
    BranchResponse,
)
from gamevcs.server.auth import get_current_user

router = APIRouter(prefix="/projects", tags=["projects"])

DEFAULT_PROJECT_NAMES = [
    "Alpha",
    "Beta",
    "Gamma",
    "Delta",
    "Epsilon",
    "Kappa",
    "Lambda",
    "Sigma",
    "Omega",
]


@router.get("", response_model=list[ProjectResponse])
def list_projects(
    db: Session = Depends(get_db), current_user: User = Depends(get_current_user)
):
    projects = db.query(Project).all()
    return [ProjectResponse.model_validate(p) for p in projects]


@router.post("", response_model=ProjectResponse)
def create_project(
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if project_data.name.isdigit():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project name cannot be a number",
        )

    existing = db.query(Project).filter(Project.name == project_data.name).first()
    if existing:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Project name already exists",
        )

    project = Project(name=project_data.name, description=project_data.description)
    db.add(project)
    db.commit()
    db.refresh(project)

    # Create default branch
    branch = Branch(project_id=project.id, name="main", description="Default branch")
    db.add(branch)
    db.commit()
    db.refresh(branch)

    project.root_cl_id = None
    db.commit()

    return ProjectResponse.model_validate(project)


@router.get("/{project_id}", response_model=ProjectResponse)
def get_project(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return ProjectResponse.model_validate(project)


@router.put("/{project_id}", response_model=ProjectResponse)
def update_project(
    project_id: int,
    project_data: ProjectCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    if project_data.name != project.name:
        if project_data.name.isdigit():
            raise HTTPException(
                status_code=400, detail="Project name cannot be a number"
            )
        existing = db.query(Project).filter(Project.name == project_data.name).first()
        if existing:
            raise HTTPException(status_code=400, detail="Project name already exists")
        project.name = project_data.name

    project.description = project_data.description
    db.commit()
    db.refresh(project)
    return ProjectResponse.model_validate(project)


@router.get("/{project_id}/branches", response_model=list[BranchResponse])
def list_branches(
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branches = db.query(Branch).filter(Branch.project_id == project_id).all()
    return [BranchResponse.model_validate(b) for b in branches]


@router.post("/{project_id}/branches", response_model=BranchResponse)
def create_branch(
    project_id: int,
    branch_data: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    existing = (
        db.query(Branch)
        .filter(Branch.project_id == project_id, Branch.name == branch_data.name)
        .first()
    )
    if existing:
        raise HTTPException(
            status_code=400, detail="Branch name already exists in this project"
        )

    branch = Branch(
        project_id=project_id,
        name=branch_data.name,
        description=branch_data.description,
        root_cl_id=branch_data.root_cl_id,
    )
    db.add(branch)
    db.commit()
    db.refresh(branch)
    return BranchResponse.model_validate(branch)
