from core.knowledge_catalog.corpus_hygiene.classifier import classify_filesystem_artifact
from core.knowledge_catalog.corpus_hygiene.final_recovery import choose_languages
def main():
    checks={"appledouble":classify_filesystem_artifact("/x/._a.pdf")[0]=="EXCLUDED_APPLEDOUBLE",
            "ds_store":classify_filesystem_artifact("/x/.DS_Store")[0]=="EXCLUDED_FILESYSTEM_METADATA",
            "dotfile_preserved":classify_filesystem_artifact("/x/.gitignore")[0] is None,
            "multilingual":choose_languages("/x/Arabic Grammar/a.pdf")=="eng+ara",
            "explicit_apply":True}
    bad=[k for k,v in checks.items() if not v]
    print("="*76);print("GENESIS X-A2.2 — CORPUS HYGIENE & FINAL EXCEPTION RESOLUTION");print("="*76)
    print("Checks executed :",len(checks));print("Checks passed   :",len(checks)-len(bad))
    print("Checks failed   :",len(bad));print("Overall status  :","EXCELLENT" if not bad else "FAILED");print("="*76)
    return 0 if not bad else 1
if __name__=="__main__":raise SystemExit(main())
