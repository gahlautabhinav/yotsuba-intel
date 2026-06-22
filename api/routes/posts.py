from fastapi import APIRouter, Depends
from api.dependencies import get_repo

router = APIRouter()


def _to_dict(obj) -> dict:
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}


@router.get("/{post_id}")
def get_post(post_id: int, repo=Depends(get_repo)):
    post = repo.get_post(post_id)
    if post is None:
        from fastapi import HTTPException
        raise HTTPException(404, "Post not found")
    return _to_dict(post)


@router.get("/{post_id}/links")
def get_post_links(post_id: int, repo=Depends(get_repo)):
    links = repo.get_links_by_post_ids([post_id])
    return [_to_dict(lk) for lk in links]
