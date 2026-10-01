from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from src.auth.router import require_admin
import src.prompts as prompt_store

router = APIRouter(prefix="/prompts", tags=["prompts"])


class PromptSection(BaseModel):
    system: str | None = None
    max_tokens: int | None = None


class PromptsPayload(BaseModel):
    general:          PromptSection | None = None
    technical:        PromptSection | None = None
    context_commands: PromptSection | None = None


# ── GET /api/prompts ─────────────────────────────────────────────────────────
@router.get("")
def get_prompts(_: dict = Depends(require_admin)):
    """Return the current merged prompt config (YAML + defaults)."""
    return prompt_store.get_all()


# ── PUT /api/prompts ─────────────────────────────────────────────────────────
@router.put("")
def update_prompts(payload: PromptsPayload, _: dict = Depends(require_admin)):
    """
    Overwrite prompts.yaml with the provided sections and hot-reload.
    Only provided fields are written — missing sections keep their current values.
    """
    current = prompt_store.get_all()

    if payload.general:
        if payload.general.system is not None:
            current["general"]["system"] = payload.general.system
        if payload.general.max_tokens is not None:
            current["general"]["max_tokens"] = payload.general.max_tokens

    if payload.technical:
        if payload.technical.system is not None:
            current["technical"]["system"] = payload.technical.system
        if payload.technical.max_tokens is not None:
            current["technical"]["max_tokens"] = payload.technical.max_tokens

    if payload.context_commands:
        if payload.context_commands.max_tokens is not None:
            current["context_commands"]["max_tokens"] = payload.context_commands.max_tokens

    try:
        prompt_store.save(current)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to save prompts: {e}")

    return {"message": "Prompts updated and reloaded", "config": prompt_store.get_all()}


# ── POST /api/prompts/reload ─────────────────────────────────────────────────
@router.post("/reload")
def reload_prompts(_: dict = Depends(require_admin)):
    """Hot-reload prompts.yaml from disk without restarting the server."""
    config = prompt_store.reload()
    return {"message": "Prompts reloaded", "config": config}
