from __future__ import annotations

import os

import httpx
from fastapi import APIRouter

router = APIRouter(prefix="/api/v1/hipporag", tags=["hipporag"])

HIPPORAG_URL = os.getenv("HIPPORAG_URL", "http://localhost:8000")


@router.get("/status")
async def hipporag_status():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.get(f"{HIPPORAG_URL}/health", timeout=3.0)
            res.raise_for_status()
            return {"status": "online", "details": res.json()}
    except Exception:
        return {"status": "offline"}


@router.post("/reconcile")
async def hipporag_reconcile():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{HIPPORAG_URL}/reconcile", timeout=10.0)
            res.raise_for_status()
            return res.json()
    except Exception:
        return {"status": "error", "message": "HippoRAG reconcile failed."}


@router.post("/rebuild")
async def hipporag_rebuild():
    try:
        async with httpx.AsyncClient() as client:
            res = await client.post(f"{HIPPORAG_URL}/rebuild", timeout=10.0)
            res.raise_for_status()
            return res.json()
    except Exception:
        return {"status": "error", "message": "HippoRAG rebuild failed."}
