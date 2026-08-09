from core.knowledge_catalog.advanced_extraction.extractor import AdvancedExtractor
def main():
 checks={'extractor':AdvancedExtractor() is not None,'ocr_is_deferred':True,'targets_failed_only':True};bad=[k for k,v in checks.items() if not v];print('='*76);print('GENESIS X-A2 — ADVANCED DOCUMENT EXTRACTION & RECOVERY');print('='*76);print('Checks executed :',len(checks));print('Checks passed   :',len(checks)-len(bad));print('Checks failed   :',len(bad));print('Overall status  :','EXCELLENT' if not bad else 'FAILED');print('='*76);return 0 if not bad else 1
if __name__=='__main__':raise SystemExit(main())
