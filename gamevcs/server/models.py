from datetime import datetime
from enum import Enum
from typing import Optional
from sqlalchemy import (
    String,
    Integer,
    Boolean,
    DateTime,
    ForeignKey,
    Text,
    Float,
    Enum as SQLEnum,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from pydantic import BaseModel


class Base(DeclarativeBase):
    pass


class UserRole(str, Enum):
    ADMIN = "admin"
    MANAGER = "manager"
    NORMAL = "normal"


class ChangelistStatus(str, Enum):
    WORKSPACE = "workspace"
    SHELVED = "shelved"
    COMMITTED = "committed"


class FileOperation(str, Enum):
    ADD = "add"
    MODIFY = "modify"
    DELETE = "delete"


class LockStatus(str, Enum):
    ACTIVE = "active"
    PENDING = "pending"
    RELEASED = "released"


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    username: Mapped[str] = mapped_column(String(255), nullable=False)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[UserRole] = mapped_column(SQLEnum(UserRole), default=UserRole.NORMAL)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    changelists: Mapped[list["Changelist"]] = relationship(
        "Changelist", back_populates="user"
    )
    locks: Mapped[list["FileLock"]] = relationship("FileLock", back_populates="user")


class Project(Base):
    __tablename__ = "projects"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(255), unique=True, nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    branches: Mapped[list["Branch"]] = relationship(
        "Branch", back_populates="project", cascade="all, delete-orphan"
    )
    changelists: Mapped[list["Changelist"]] = relationship(
        "Changelist", back_populates="project"
    )
    tags: Mapped[list["Tag"]] = relationship("Tag", back_populates="project")


class Branch(Base):
    __tablename__ = "branches"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    root_cl_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="branches")
    changelists: Mapped[list["Changelist"]] = relationship(
        "Changelist", back_populates="branch"
    )


class Changelist(Base):
    __tablename__ = "changelists"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    branch_id: Mapped[int] = mapped_column(ForeignKey("branches.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    parent_cl_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    message: Mapped[str] = mapped_column(Text, default="")
    status: Mapped[ChangelistStatus] = mapped_column(
        SQLEnum(ChangelistStatus), default=ChangelistStatus.WORKSPACE
    )
    is_shelf: Mapped[bool] = mapped_column(Boolean, default=False)
    shelf_parent_cl_id: Mapped[Optional[int]] = mapped_column(Integer, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    committed_at: Mapped[Optional[datetime]] = mapped_column(DateTime, nullable=True)

    project: Mapped["Project"] = relationship("Project", back_populates="changelists")
    branch: Mapped["Branch"] = relationship("Branch", back_populates="changelists")
    user: Mapped["User"] = relationship("User", back_populates="changelists")
    files: Mapped[list["File"]] = relationship(
        "File", back_populates="changelist", cascade="all, delete-orphan"
    )


class File(Base):
    __tablename__ = "files"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    changelist_id: Mapped[int] = mapped_column(
        ForeignKey("changelists.id"), nullable=False
    )
    path: Mapped[str] = mapped_column(String(1024), nullable=False)
    hash: Mapped[str] = mapped_column(String(64), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    operation: Mapped[FileOperation] = mapped_column(
        SQLEnum(FileOperation), default=FileOperation.ADD
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    changelist: Mapped["Changelist"] = relationship(
        "Changelist", back_populates="files"
    )
    locks: Mapped[list["FileLock"]] = relationship(
        "FileLock", back_populates="file", cascade="all, delete-orphan"
    )


class FileLock(Base):
    __tablename__ = "file_locks"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    file_id: Mapped[int] = mapped_column(ForeignKey("files.id"), nullable=False)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), nullable=False)
    queue_position: Mapped[int] = mapped_column(Integer, default=1)
    status: Mapped[LockStatus] = mapped_column(
        SQLEnum(LockStatus), default=LockStatus.PENDING
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    file: Mapped["File"] = relationship("File", back_populates="locks")
    user: Mapped["User"] = relationship("User", back_populates="locks")


class Tag(Base):
    __tablename__ = "tags"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    project_id: Mapped[int] = mapped_column(ForeignKey("projects.id"), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    changelist_id: Mapped[int] = mapped_column(
        ForeignKey("changelists.id"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)

    project: Mapped["Project"] = relationship("Project", back_populates="tags")
    changelist: Mapped["Changelist"] = relationship("Changelist")


# Pydantic schemas
class UserCreate(BaseModel):
    email: str
    username: str
    password: str
    role: UserRole = UserRole.NORMAL


class UserResponse(BaseModel):
    id: int
    email: str
    username: str
    role: UserRole
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    email: Optional[str] = None
    username: Optional[str] = None
    new_role: Optional[UserRole] = None
    is_active: Optional[bool] = None
    reset_password: Optional[bool] = None
    password: Optional[str] = None


class ProjectCreate(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


class BranchCreate(BaseModel):
    project_id: int
    name: str
    description: Optional[str] = None
    root_cl_id: Optional[int] = None


class BranchResponse(BaseModel):
    id: int
    project_id: int
    name: str
    description: Optional[str]
    root_cl_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class ChangelistCreate(BaseModel):
    project_id: int
    branch_id: int
    message: str = ""
    parent_cl_id: Optional[int] = None


class ChangelistResponse(BaseModel):
    id: int
    project_id: int
    branch_id: int
    user_id: int
    parent_cl_id: Optional[int]
    message: str
    status: ChangelistStatus
    is_shelf: bool
    shelf_parent_cl_id: Optional[int]
    created_at: datetime
    committed_at: Optional[datetime]

    class Config:
        from_attributes = True


class FileCreate(BaseModel):
    changelist_id: int
    path: str
    hash: str
    size: int
    operation: FileOperation = FileOperation.ADD


class FileResponse(BaseModel):
    id: int
    changelist_id: int
    path: str
    hash: str
    size: int
    operation: FileOperation
    created_at: datetime

    class Config:
        from_attributes = True


class LockCreate(BaseModel):
    file_id: int


class LockResponse(BaseModel):
    id: int
    file_id: int
    user_id: int
    queue_position: int
    status: LockStatus
    created_at: datetime

    class Config:
        from_attributes = True


class TagCreate(BaseModel):
    project_id: int
    name: str
    changelist_id: int
    allow_move: bool = False


class TagResponse(BaseModel):
    id: int
    project_id: int
    name: str
    changelist_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class LoginRequest(BaseModel):
    email: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class CommitRequest(BaseModel):
    message: str
    keep_locks: bool = False


class ShelveRequest(BaseModel):
    message: str


class MergeRequest(BaseModel):
    source_branch_id: int
    target_cl_id: Optional[int] = None


class AddFilesRequest(BaseModel):
    paths: list[str]
