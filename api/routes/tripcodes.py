import dataclasses
from fastapi import APIRouter, Depends
from api.dependencies import get_repo

router = APIRouter()


def _to_dict(obj) -> dict:
    return {k: v for k, v in obj.__dict__.items() if not k.startswith("_")}


@router.get("/")
def list_tripcodes(repo=Depends(get_repo)):
    return [_to_dict(t) for t in repo.list_tripcodes()]


@router.get("/{trip}/profile")
def get_tripcode_profile(trip: str, repo=Depends(get_repo)):
    from analysis.tripcode_profiler import profile_trip
    tc = repo.get_tripcode(trip)
    if tc is None:
        from fastapi import HTTPException
        raise HTTPException(404, f"Tripcode {trip} not found")
    profile = profile_trip(trip)
    return dataclasses.asdict(profile)
