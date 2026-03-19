from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from gamevcs.server.database import get_db
from gamevcs.server.models import (
    User,
    FileLock,
    File,
    Changelist,
    ChangelistStatus,
    LockCreate,
    LockResponse,
)
from gamevcs.server.auth import get_current_user

router = APIRouter(prefix="/locks", tags=["locks"])


@router.get("", response_model=list[LockResponse])
def list_locks(
    file_id: int = None,
    changelist_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(FileLock)

    if file_id:
        query = query.filter(FileLock.file_id == file_id)
    elif changelist_id:
        files = db.query(File).filter(File.changelist_id == changelist_id).all()
        file_ids = [f.id for f in files]
        query = query.filter(FileLock.file_id.in_(file_ids))

    locks = query.all()
    return [LockResponse.model_validate(l) for l in locks]


@router.post("", response_model=LockResponse)
def request_lock(
    lock_data: LockCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    file = db.query(File).filter(File.id == lock_data.file_id).first()
    if not file:
        raise HTTPException(status_code=404, detail="File not found")

    existing_lock = (
        db.query(FileLock)
        .filter(
            FileLock.file_id == lock_data.file_id,
            FileLock.user_id == current_user.id,
            FileLock.status.in_(["active", "pending"]),
        )
        .first()
    )

    if existing_lock:
        raise HTTPException(
            status_code=400, detail="You already have a lock on this file"
        )

    max_queue = (
        db.query(FileLock)
        .filter(FileLock.file_id == lock_data.file_id, FileLock.status == "pending")
        .order_by(FileLock.queue_position.desc())
        .first()
    )

    new_position = (max_queue.queue_position + 1) if max_queue else 1

    active_locks = (
        db.query(FileLock)
        .filter(FileLock.file_id == lock_data.file_id, FileLock.status == "active")
        .count()
    )

    lock_status = "active" if active_locks == 0 else "pending"

    file_lock = FileLock(
        file_id=lock_data.file_id,
        user_id=current_user.id,
        queue_position=new_position,
        status=lock_status,
    )
    db.add(file_lock)
    db.commit()
    db.refresh(file_lock)

    return LockResponse.model_validate(file_lock)


@router.delete("/{lock_id}")
def release_lock(
    lock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lock = db.query(FileLock).filter(FileLock.id == lock_id).first()
    if not lock:
        raise HTTPException(status_code=404, detail="Lock not found")

    if lock.user_id != current_user.id and current_user.role.value not in [
        "admin",
        "manager",
    ]:
        raise HTTPException(
            status_code=403, detail="Not authorized to release this lock"
        )

    file_id = lock.file_id
    lock.status = "released"

    db.commit()

    next_pending = (
        db.query(FileLock)
        .filter(FileLock.file_id == file_id, FileLock.status == "pending")
        .order_by(FileLock.queue_position.asc())
        .first()
    )

    if next_pending:
        next_pending.status = "active"
        db.commit()

    return {"message": "Lock released"}


@router.post("/{lock_id}/request-ownership")
def request_ownership(
    lock_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lock = db.query(FileLock).filter(FileLock.id == lock_id).first()
    if not lock:
        raise HTTPException(status_code=404, detail="Lock not found")

    if lock.status != "active":
        raise HTTPException(
            status_code=400, detail="Can only request ownership of active locks"
        )

    if lock.user_id == current_user.id:
        raise HTTPException(status_code=400, detail="You already own this lock")

    existing_request = (
        db.query(FileLock)
        .filter(
            FileLock.file_id == lock.file_id,
            FileLock.user_id == current_user.id,
            FileLock.status == "pending",
        )
        .first()
    )

    if existing_request:
        raise HTTPException(status_code=400, detail="You already requested this lock")

    max_queue = (
        db.query(FileLock)
        .filter(FileLock.file_id == lock.file_id, FileLock.status == "pending")
        .order_by(FileLock.queue_position.desc())
        .first()
    )

    new_position = (max_queue.queue_position + 1) if max_queue else 1

    new_lock = FileLock(
        file_id=lock.file_id,
        user_id=current_user.id,
        queue_position=new_position,
        status="pending",
        request_from=lock.user_id,
    )
    db.add(new_lock)
    db.commit()

    return {"message": "Lock ownership request sent", "lock_id": new_lock.id}


@router.post("/{lock_id}/respond")
def respond_to_ownership_request(
    lock_id: int,
    approve: bool,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    lock = db.query(FileLock).filter(FileLock.id == lock_id).first()
    if not lock:
        raise HTTPException(status_code=404, detail="Lock not found")

    if lock.user_id != current_user.id:
        raise HTTPException(
            status_code=403, detail="Not authorized to respond to this request"
        )

    if lock.status != "active":
        raise HTTPException(status_code=400, detail="Lock is not active")

    pending_requests = (
        db.query(FileLock)
        .filter(
            FileLock.file_id == lock.file_id,
            FileLock.status == "pending",
            FileLock.request_from == current_user.id,
        )
        .all()
    )

    if approve and pending_requests:
        approved = pending_requests[0]
        lock.status = "released"
        approved.status = "active"

    db.commit()

    return {"message": "Request processed" if approve else "Request denied"}
