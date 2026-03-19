from datetime import datetime
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from gamevcs.server.database import get_db
from gamevcs.server.models import (
    User,
    Branch,
    Changelist,
    ChangelistStatus,
    BranchCreate,
    BranchResponse,
    ChangelistResponse,
    MergeRequest,
)
from gamevcs.server.auth import get_current_user

router = APIRouter(prefix="/branches", tags=["branches"])


@router.get("", response_model=list[BranchResponse])
def list_branches(
    project_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Branch)
    if project_id:
        query = query.filter(Branch.project_id == project_id)
    branches = query.all()
    return [BranchResponse.model_validate(b) for b in branches]


@router.get("/{branch_id}", response_model=BranchResponse)
def get_branch(
    branch_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")
    return BranchResponse.model_validate(branch)


@router.put("/{branch_id}", response_model=BranchResponse)
def update_branch(
    branch_id: int,
    branch_data: BranchCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    if branch_data.name:
        existing = (
            db.query(Branch)
            .filter(
                Branch.project_id == branch.project_id,
                Branch.name == branch_data.name,
                Branch.id != branch_id,
            )
            .first()
        )
        if existing:
            raise HTTPException(status_code=400, detail="Branch name already exists")
        branch.name = branch_data.name

    if branch_data.description is not None:
        branch.description = branch_data.description

    db.commit()
    db.refresh(branch)
    return BranchResponse.model_validate(branch)


@router.post("/{branch_id}/merge", response_model=ChangelistResponse)
def merge_branch(
    branch_id: int,
    merge_data: MergeRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    target_branch = db.query(Branch).filter(Branch.id == branch_id).first()
    if not target_branch:
        raise HTTPException(status_code=404, detail="Target branch not found")

    source_branch = (
        db.query(Branch).filter(Branch.id == merge_data.source_branch_id).first()
    )
    if not source_branch:
        raise HTTPException(status_code=404, detail="Source branch not found")

    target_cl_id = merge_data.target_cl_id
    if not target_cl_id:
        target_cl = (
            db.query(Changelist)
            .filter(
                Changelist.branch_id == branch_id,
                Changelist.status == ChangelistStatus.COMMITTED,
            )
            .order_by(Changelist.id.desc())
            .first()
        )
        target_cl_id = target_cl.id if target_cl else None

    new_cl = Changelist(
        project_id=target_branch.project_id,
        branch_id=branch_id,
        user_id=current_user.id,
        parent_cl_id=target_cl_id,
        message=f"Merge from branch '{source_branch.name}'",
        status=ChangelistStatus.WORKSPACE,
    )
    db.add(new_cl)
    db.commit()
    db.refresh(new_cl)

    return ChangelistResponse.model_validate(new_cl)
