from pathlib import Path
from core.knowledge_catalog.ocr_recovery.models import OCRPolicy
from core.knowledge_catalog.ocr_recovery.service import OCRRecoveryService

ARABIC_HINTS=("arabic","mawrid","wortbat","wrightarabic","aric")

def choose_languages(path:str)->str:
    lower=path.casefold()
    return "eng+ara" if any(x in lower for x in ARABIC_HINTS) else "eng"

def policy_excluded(path:str)->bool:
    name=Path(path).name.casefold()
    return "full-auto conversion" in name or "select fire ak-47" in name

def make_service(runtime_catalog,checkpoint_db,recovery_db,work_dir,path_hint):
    return OCRRecoveryService(runtime_catalog=runtime_catalog,checkpoint_db=checkpoint_db,
      recovery_db=recovery_db,work_dir=work_dir,
      policy=OCRPolicy(dpi=200,max_pages=120,max_seconds_per_page=45,
                       minimum_chars=120,minimum_quality=.45,languages=choose_languages(path_hint)))
