from typing import Optional
from fastapi import APIRouter, Depends
from pydantic import BaseModel
from api.dependencies import get_repo

router = APIRouter()


class ArchiveSearchRequest(BaseModel):
    trip: Optional[str] = None
    md5: Optional[str] = None
    name: Optional[str] = None
    sources: Optional[list[str]] = None
    board: Optional[str] = None


@router.post("/search")
def archive_search(req: ArchiveSearchRequest, repo=Depends(get_repo)):
    from scraper.archive_client import ArchiveClient
    client = ArchiveClient()
    results = []
    if req.trip:
        results = client.search_by_trip(req.trip, sources=req.sources)
    elif req.md5:
        results = client.search_by_md5(req.md5, sources=req.sources)
    elif req.name:
        results = client.search_by_name(req.name, board=req.board, sources=req.sources)
    else:
        from fastapi import HTTPException
        raise HTTPException(400, "Provide trip, md5, or name")
    return results
