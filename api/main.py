from contextlib import asynccontextmanager
from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from storage.engine import init_db

from api.routes import threads, posts, links, emails, tripcodes, archive, correlate, scrape as scrape_router
from api.dependencies import get_repo


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield


app = FastAPI(title="Yotsuba Intel API", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(threads.router, prefix="/threads", tags=["threads"])
app.include_router(posts.router, prefix="/posts", tags=["posts"])
app.include_router(links.router, prefix="/links", tags=["links"])
app.include_router(emails.router, prefix="/emails", tags=["emails"])
app.include_router(tripcodes.router, prefix="/tripcodes", tags=["tripcodes"])
app.include_router(archive.router, prefix="/archive", tags=["archive"])
app.include_router(correlate.router, prefix="/correlate", tags=["correlate"])
app.include_router(scrape_router.router, prefix="/scrape", tags=["scrape"])


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/stats")
def stats(repo=Depends(get_repo)):
    threads_list = repo.list_threads()
    tripcodes_list = repo.list_tripcodes()
    return {
        "thread_count": len(threads_list),
        "tripcode_count": len(tripcodes_list),
    }
