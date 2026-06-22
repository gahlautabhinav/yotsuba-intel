from fastapi import APIRouter, Depends
from api.dependencies import get_repo

router = APIRouter()


def _to_dict(obj) -> dict:
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}


@router.get("/")
def list_threads(repo=Depends(get_repo)):
    return [_to_dict(t) for t in repo.list_threads()]


@router.get("/{thread_id}")
def get_thread(thread_id: int, repo=Depends(get_repo)):
    threads = repo.list_threads()
    for t in threads:
        if t.id == thread_id:
            return _to_dict(t)
    from fastapi import HTTPException
    raise HTTPException(404, "Thread not found")


@router.get("/{thread_id}/posts")
def get_thread_posts(thread_id: int, repo=Depends(get_repo)):
    return [_to_dict(p) for p in repo.get_posts_by_thread(thread_id)]


@router.get("/{thread_id}/links")
def get_thread_links(thread_id: int, repo=Depends(get_repo)):
    rows = repo.get_pivot_results_by_thread(thread_id)
    result = []
    for lk, pr in rows:
        d = _to_dict(lk)
        d["pivot_status"] = pr.status if pr else "pending"
        d["pivot_profile_data"] = pr.profile_data if pr else None
        result.append(d)
    return result


@router.get("/{thread_id}/emails")
def get_thread_emails(thread_id: int, repo=Depends(get_repo)):
    return [_to_dict(e) for e in repo.get_emails_by_thread(thread_id)]
