from typing import Optional
from fastapi import APIRouter, Depends
from api.dependencies import get_repo

router = APIRouter()


def _to_dict(obj) -> dict:
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}


@router.get("/")
def list_emails(thread_id: Optional[int] = None, repo=Depends(get_repo)):
    if thread_id:
        return [_to_dict(e) for e in repo.get_emails_by_thread(thread_id)]
    from storage import models
    from storage.engine import get_session
    with get_session() as session:
        return [_to_dict(e) for e in session.query(models.Email).all()]
