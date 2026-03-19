from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from gamevcs.server.database import get_db
from gamevcs.server.models import (
    User,
    Tag,
    Changelist,
    ChangelistStatus,
    TagCreate,
    TagResponse,
)
from gamevcs.server.auth import get_current_user

router = APIRouter(prefix="/tags", tags=["tags"])


@router.get("", response_model=list[TagResponse])
def list_tags(
    project_id: int = None,
    changelist_id: int = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    query = db.query(Tag)

    if project_id:
        query = query.filter(Tag.project_id == project_id)
    if changelist_id:
        query = query.filter(Tag.changelist_id == changelist_id)

    tags = query.all()
    return [TagResponse.model_validate(t) for t in tags]


@router.post("", response_model=TagResponse)
def create_tag(
    tag_data: TagCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    cl = db.query(Changelist).filter(Changelist.id == tag_data.changelist_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail="Changelist not found")

    if cl.status != ChangelistStatus.COMMITTED:
        raise HTTPException(
            status_code=400, detail="Can only tag committed changelists"
        )

    if tag_data.name in ["head", "latest", "current"] or tag_data.name.isdigit():
        raise HTTPException(status_code=400, detail="Invalid tag name")

    if tag_data.name.startswith("*"):
        raise HTTPException(status_code=400, detail="Tag name cannot start with *")

    existing = (
        db.query(Tag)
        .filter(Tag.project_id == tag_data.project_id, Tag.name == tag_data.name)
        .first()
    )

    if existing:
        if not tag_data.allow_move:
            raise HTTPException(
                status_code=400,
                detail="Tag already exists, use allow_move=true to move it",
            )
        existing.changelist_id = tag_data.changelist_id
        db.commit()
        db.refresh(existing)
        return TagResponse.model_validate(existing)

    tag = Tag(
        project_id=tag_data.project_id,
        name=tag_data.name,
        changelist_id=tag_data.changelist_id,
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)

    return TagResponse.model_validate(tag)


@router.delete("/{tag_id}")
def delete_tag(
    tag_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = db.query(Tag).filter(Tag.id == tag_id).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    db.delete(tag)
    db.commit()
    return {"message": "Tag deleted"}


@router.get("/{tag_name}/changelist")
def get_tag_changelist(
    tag_name: str,
    project_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    tag = (
        db.query(Tag).filter(Tag.name == tag_name, Tag.project_id == project_id).first()
    )

    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    cl = db.query(Changelist).filter(Changelist.id == tag.changelist_id).first()
    if not cl:
        raise HTTPException(status_code=404, detail="Changelist not found")

    return {
        "tag": TagResponse.model_validate(tag),
        "changelist": {"id": cl.id, "message": cl.message, "status": cl.status.value},
    }
