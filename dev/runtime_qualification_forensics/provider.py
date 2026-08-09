from pathlib import Path

class LiveQualificationProvider:
    def __init__(self):
        from core.knowledge_catalog.search import search_catalog
        from core.knowledge_catalog.qualified_search import (
            get_last_qualification_result,
            get_last_qualification_trace,
            search_qualified_catalog,
        )
        self._raw=search_catalog
        self._qualified=search_qualified_catalog
        self._trace=get_last_qualification_trace
        self._result=get_last_qualification_result

    def raw_search(self, query, *, database_path:Path, limit:int):
        return list(self._raw(query,db_path=database_path,limit=limit))

    def qualified_search(self, query, *, database_path:Path, limit:int):
        return list(self._qualified(query,db_path=database_path,limit=limit))

    def last_trace(self):
        return self._trace()

    def last_result(self):
        return self._result()
