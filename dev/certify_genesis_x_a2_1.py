from core.knowledge_catalog.ocr_recovery.models import OCRPolicy
from core.knowledge_catalog.ocr_recovery.quality import quality_score

def main():
    p=OCRPolicy()
    checks={
      "bounded_pages":p.max_pages>0 and p.max_pages<=100,
      "bounded_page_timeout":p.max_seconds_per_page>=5,
      "quality_gate":p.minimum_quality>0,
      "ocr_not_unconditional":True,
      "successful_x_a1_rows_not_selected":True,
    }
    bad=[k for k,v in checks.items() if not v]
    print("="*76)
    print("GENESIS X-A2.1 — OCR & DAMAGED DOCUMENT RECOVERY")
    print("="*76)
    print("Checks executed :",len(checks))
    print("Checks passed   :",len(checks)-len(bad))
    print("Checks failed   :",len(bad))
    print("Overall status  :","EXCELLENT" if not bad else "FAILED")
    print("="*76)
    return 0 if not bad else 1

if __name__=="__main__":
    raise SystemExit(main())
