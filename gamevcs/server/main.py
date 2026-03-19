import os
import sys
import argparse
from pathlib import Path
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from gamevcs.server.database import init_db, get_db
from gamevcs.server.api import auth, users, projects, branches, changelists, locks, tags


app = FastAPI(title="GameVC Server", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(users.router)
app.include_router(projects.router)
app.include_router(branches.router)
app.include_router(changelists.router)
app.include_router(locks.router)
app.include_router(tags.router)


@app.get("/")
def root():
    return {"message": "GameVC Server", "version": "0.1.0"}


@app.get("/health")
def health():
    return {"status": "healthy"}


def main():
    parser = argparse.ArgumentParser(description="GameVC Server")
    parser.add_argument(
        "-path", type=str, required=True, help="Path to server data directory"
    )
    parser.add_argument(
        "-port", type=int, default=9000, help="Port to listen on (default: 9000)"
    )
    parser.add_argument(
        "-log_level",
        type=str,
        default="info",
        choices=["debug", "info", "warning", "error"],
        help="Log level",
    )
    parser.add_argument(
        "-allow_dv_upgrade", action="store_true", help="Allow data version upgrade"
    )
    parser.add_argument(
        "-allow_non_empty_path", action="store_true", help="Allow non-empty path"
    )

    args = parser.parse_args()

    server_path = Path(args.path)

    if (
        not args.allow_non_empty_path
        and server_path.exists()
        and any(server_path.iterdir())
    ):
        print(
            f"Error: Server path is not empty. Use -allow_non_empty_path to force.",
            file=sys.stderr,
        )
        sys.exit(1)

    server_path.mkdir(parents=True, exist_ok=True)

    db_path = server_path / "gamevcs.db"
    print(f"Initializing database at {db_path}...")
    init_db(str(db_path))

    storage_path = server_path / "storage"
    storage_path.mkdir(parents=True, exist_ok=True)

    print(f"Starting GameVCS Server on port {args.port}...")
    uvicorn.run(app, host="0.0.0.0", port=args.port, log_level=args.log_level)


if __name__ == "__main__":
    main()
