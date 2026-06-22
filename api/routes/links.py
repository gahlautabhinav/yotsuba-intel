from fastapi import APIRouter, Depends
from api.dependencies import get_repo

router = APIRouter()


def _to_dict(obj) -> dict:
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}


@router.get("/")
def list_links(repo=Depends(get_repo)):
    return [_to_dict(lk) for lk in repo.get_pending_links()]


@router.get("/{link_id}/pivot")
def get_link_pivot(link_id: int, repo=Depends(get_repo)):
    from storage import models
    from storage.engine import get_session
    with get_session() as session:
        pr = session.query(models.PivotResult).filter_by(link_id=link_id).first()
        if pr is None:
            return {"status": "pending"}
        return _to_dict(pr)
