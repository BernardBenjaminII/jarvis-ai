from dev.materialization_completion_audit.audit import classify
def main():
 checks={'transient':classify('database is locked')=='TRANSIENT_RETRYABLE','corrupt':classify('EOF marker not found')=='CORRUPT_OR_MALFORMED','no_text':classify('no usable text')=='NO_EXTRACTABLE_TEXT'}; bad=[k for k,v in checks.items() if not v]
 print('='*76); print('GENESIS X-A1.3 CERTIFICATION'); print('='*76); print('Checks executed :',len(checks)); print('Checks passed   :',len(checks)-len(bad)); print('Checks failed   :',len(bad)); print('Overall status  :','EXCELLENT' if not bad else 'FAILED'); print('='*76); return 0 if not bad else 1
if __name__=='__main__':raise SystemExit(main())
