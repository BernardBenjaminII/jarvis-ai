"""On-demand platform status; static HTTPX identity check, no tool execution."""
from fastapi import APIRouter
from core.src.cognition.platform_status import snapshot
from core.bounty_worker.identity import inventory

router = APIRouter()


@router.get('/api/runtime/platform')
def platform_status() -> dict:
    data = dict(snapshot())
    identities = inventory()
    capabilities = dict(data.get('capabilities', {}))
    capabilities['httpx'] = identities['httpx'].get('recon_available', False)
    data['capabilities'] = capabilities
    data['tool_identity'] = identities
    data['capability_check'] = (
        'HTTPX uses static identity inspection; other flags retain executable-presence semantics. '
        'No tool readiness or testing authorization is established.'
    )
    return data
