import os
import shutil
from datetime import datetime
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, status
from sqlalchemy.orm import Session
from gamevcs.server.database import get_db
from gamevcs.server.models import (
    User,
    Project,
    Branch,
    Changelist,
    ChangelistStatus,
    File as FileModel,
    FileOperation,
    ChangelistCreate,
    ChangelistResponse,
    CommitRequest,
    ShelveRequest,
)
from gamevcs.server.auth import get_current_user

router = APIRouter(prefix="/changelists", tags=["changelists"])


def get_storage_path(project_id: int, branch_id: int, changelist_id: int) -> Path:
    base = Path(__file__).parent.parent / "storage"
    return base / str(project_id) / str(branch_id) / str(changelist_id)


@router.get("", response_model=list[ChangelistResponse])
def list_changelists(
    project_id: int = None,
    branch_id: int = None,
    status: ChangelistStatus = None,
    is_shelf: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Changelist)
    if project_id:
        query = query.filter(Changelist.project_id == project_id)
    if branch_id:
        query = query.filter(Changelist.branch_id == branch_id)
    if status:
        query = query.filter(Changelist.status == status)
    if is_shelf is not None:
        query = query.filter(Changelist.is_shelf == is_shelf)

    changelists = query.order_by(Changelist.id.desc()).all()
    return [ChangelistResponse.model_validate(c) for c in changelists]


@router.post("", response_model=ChangelistResponse)
def create_changelist(
    cl_data: ChangelistCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    project = db.query(Project).filter(Project.id == cl_data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    branch = (
        db.query(Branch)
        .filter(Branch.id == cl_data.branch_id, Branch.project_id == cl_data.project_id)
        .first()
    )
    if not branch:
        raise HTTPException(status_code=404, detail="Branch not found")

    changelist = Changelist(
        project_id=cl_data.project_id,
        branch_id=cl_data.branch_id,
        user_id=current_user.id,
        parent_cl_id=cl_data.parent_cl_id,
        message=cl_data.message,
        status=ChangelistStatus.WORKSPACE,
    )
    db.add(changelist)
    db.commit()
    db.refresh(changelist)

    storage_path = get_storage_path(
        cl_data.project_id, cl_data.branch_id, changelist.id
    )
    storage_path.mkdir(parents=True, exist_ok=True)

    return ChangelistResponse.model_validate(changelist)


@router.get("/{changelist_id}", response_model=ChangelistResponse)
def get_changelist(
    changelist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cl = db.query(Changelist).filter(Changelist.id == changelist_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail="Changelist not found")
    return ChangelistResponse.model_validate(cl)


@router.put("/{changelist_id}", response_model=ChangelistResponse)
def update_changelist(
    changelist_id: int,
    message: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cl = db.query(Changelist).filter(Changelist.id == changelist_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail="Changelist not found")

    if cl.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to modify this changelist"
        )

    cl.message = message
    db.commit()
    db.refresh(cl)
    return ChangelistResponse.model_validate(cl)


@router.post("/{changelist_id}/commit", response_model=ChangelistResponse)
def commit_changelist(
    changelist_id: int,
    commit_data: CommitRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cl = db.query(Changelist).filter(Changelist.id == changelist_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail="Changelist not found")

    if cl.status == ChangelistStatus.COMMITTED:
        raise HTTPException(status_code=400, detail="Changelist already committed")

    if cl.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to commit this changelist"
        )

    cl.status = ChangelistStatus.COMMITTED
    cl.committed_at = datetime.utcnow()
    cl.message = commit_data.message or cl.message

    project = db.query(Project).filter(Project.id == cl.project_id).first()
    branch = db.query(Branch).filter(Branch.id == cl.branch_id).first()

    storage_path = get_storage_path(cl.project_id, cl.branch_id, cl.id)
    committed_path = get_storage_path(cl.project_id, cl.branch_id, "committed")
    committed_path = committed_path / str(cl.id)

    if storage_path.exists():
        shutil.move(str(storage_path), str(committed_path))

    if not commit_data.keep_locks:
        for file in cl.files:
            for lock in file.locks:
                if lock.user_id == current_user.id:
                    lock.status = "released"

    db.commit()
    db.refresh(cl)
    return ChangelistResponse.model_validate(cl)


@router.post("/{changelist_id}/shelve", response_model=ChangelistResponse)
def shelve_changelist(
    changelist_id: int,
    shelve_data: ShelveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cl = db.query(Changelist).filter(Changelist.id == changelist_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail="Changelist not found")

    if cl.status != ChangelistStatus.WORKSPACE:
        raise HTTPException(
            status_code=400, detail="Only workspace changelists can be shelved"
        )

    if cl.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to shelve this changelist"
        )

    cl.status = ChangelistStatus.SHELVED
    cl.is_shelf = True
    cl.shelf_parent_cl_id = cl.parent_cl_id
    cl.message = shelve_data.message or cl.message

    db.commit()
    db.refresh(cl)
    return ChangelistResponse.model_validate(cl)


@router.delete("/{changelist_id}")
def delete_changelist(
    changelist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cl = db.query(Changelist).filter(Changelist.id == changelist_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail="Changelist not found")

    if cl.user_id != current_user.id and current_user.role.value not in [
        "admin",
        "manager",
    ]:
        raise HTTPException(
            status_code=403, detail="Not authorized to delete this changelist"
        )

    storage_path = get_storage_path(cl.project_id, cl.branch_id, cl.id)
    if storage_path.exists():
        shutil.rmtree(storage_path)

    db.delete(cl)
    db.commit()
    return {"message": "Changelist deleted"}


@router.get("/{changelist_id}/files", response_model=list[dict])
def get_changelist_files(
    changelist_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cl = db.query(Changelist).filter(Changelist.id == changelist_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail="Changelist not found")

    files = db.query(FileModel).filter(FileModel.changelist_id == changelist_id).all()
    result = []
    for f in files:
        lock_info = None
        active_locks = [l for l in f.locks if l.status == "active"]
        if active_locks:
            lock_info = {
                "user_id": active_locks[0].user_id,
                "username": active_locks[0].user.username,
                "queue_position": active_locks[0].queue_position,
            }

        result.append(
            {
                "id": f.id,
                "path": f.path,
                "hash": f.hash,
                "size": f.size,
                "operation": f.operation.value,
                "lock": lock_info,
            }
        )

    return result


@router.post("/{changelist_id}/files")
async def upload_file(
    changelist_id: int,
    path: str = Form(...),
    operation: str = Form("add"),
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cl = db.query(Changelist).filter(Changelist.id == changelist_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail="Changelist not found")

    if cl.status != ChangelistStatus.WORKSPACE:
        raise HTTPException(
            status_code=400, detail="Can only add files to workspace changelists"
        )

    content = await file.read()
    size = len(content)

    import xxhash

    file_hash = xxhash.xxh64(content).hexdigest()

    storage_path = get_storage_path(cl.project_id, cl.branch_id, cl.id)
    storage_path.mkdir(parents=True, exist_ok=True)

    safe_path = storage_path / file_hash
    with open(safe_path, "wb") as f:
        f.write(content)

    existing_file = (
        db.query(FileModel)
        .filter(FileModel.changelist_id == changelist_id, FileModel.path == path)
        .first()
    )

    if existing_file:
        existing_file.hash = file_hash
        existing_file.size = size
        existing_file.operation = operation
        db.refresh(existing_file)
        return {
            "message": "File updated",
            "file_id": existing_file.id,
            "hash": file_hash,
        }

    file_record = FileModel(
        changelist_id=changelist_id,
        path=path,
        hash=file_hash,
        size=size,
        operation=operation,
    )
    db.add(file_record)
    db.commit()
    db.refresh(file_record)

    return {"message": "File added", "file_id": file_record.id, "hash": file_hash}


@router.get("/{changelist_id}/files/{file_id}/download")
async def download_file(
    changelist_id: int,
    file_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file_record = (
        db.query(FileModel)
        .filter(FileModel.id == file_id, FileModel.changelist_id == changelist_id)
        .first()
    )

    if not file_record:
        raise HTTPException(status_code=404, detail="File not found")

    storage_path = get_storage_path(
        file_record.changelist.project_id,
        file_record.changelist.branch_id,
        changelist_id,
    )
    file_path = storage_path / file_record.hash

    if not file_path.exists():
        storage_path = get_storage_path(
            file_record.changelist.project_id,
            file_record.changelist.branch_id,
            "committed",
        )
        file_path = storage_path / str(changelist_id) / file_record.hash

    if not file_path.exists():
        raise HTTPException(status_code=404, detail="File content not found")

    return {
        "path": file_record.path,
        "hash": file_record.hash,
        "size": file_record.size,
    }
