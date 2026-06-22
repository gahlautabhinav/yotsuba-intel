import dataclasses
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter()


class CorrelateRequest(BaseModel):
    md5: str


@router.post("/md5")
def correlate_md5_route(req: CorrelateRequest):
    from analysis.md5_correlator import correlate_md5
    result = correlate_md5(req.md5)
    # result["post_refs"] is list[PostRef] dataclasses — convert each to dict
    result["post_refs"] = [dataclasses.asdict(ref) for ref in result["post_refs"]]
    return result
