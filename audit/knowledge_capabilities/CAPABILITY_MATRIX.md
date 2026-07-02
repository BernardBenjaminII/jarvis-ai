# JARVIS Knowledge Capability Matrix

Generated from repository source code.

## Package Summary

| Package | Modules | Classes | Functions | CLI | DB | Capabilities |
|---|---:|---:|---:|---:|---:|---|
| core/knowledge_catalog | 18 | 6 | 43 | 2 | 9 | acquisition, catalog, chunking, classification, collections, embedding, extraction, graph, inspection, normalization, search, storage |
| core/knowledge_graph | 8 | 2 | 10 | 1 | 1 | catalog, classification, extraction, graph, storage |
| core/knowledge_mapper | 7 | 0 | 4 | 1 | 0 | classification, collections, extraction |
| core/semantic_digest | 7 | 1 | 15 | 1 | 0 | catalog, chunking, classification, collections, extraction, graph, inspection, normalization |
| dev/librarian | 24 | 4 | 64 | 7 | 2 | acquisition, catalog, chunking, cko, classification, collections, extraction, graph, inspection, normalization, search, storage |
| knowledge_engine | 95 | 40 | 62 | 1 | 14 | acquisition, catalog, chunking, classification, collections, embedding, extraction, graph, inspection, normalization, search, storage |

## Capability Ownership

| Capability | Owners | Duplication Risk |
|---|---|---|
| acquisition | core/knowledge_catalog, dev/librarian, knowledge_engine | HIGH |
| catalog | core/knowledge_catalog, core/knowledge_graph, core/semantic_digest, dev/librarian, knowledge_engine | HIGH |
| chunking | core/knowledge_catalog, core/semantic_digest, dev/librarian, knowledge_engine | HIGH |
| cko | dev/librarian | LOW |
| classification | core/knowledge_catalog, core/knowledge_graph, core/knowledge_mapper, core/semantic_digest, dev/librarian, knowledge_engine | HIGH |
| collections | core/knowledge_catalog, core/knowledge_mapper, core/semantic_digest, dev/librarian, knowledge_engine | HIGH |
| embedding | core/knowledge_catalog, knowledge_engine | HIGH |
| extraction | core/knowledge_catalog, core/knowledge_graph, core/knowledge_mapper, core/semantic_digest, dev/librarian, knowledge_engine | HIGH |
| graph | core/knowledge_catalog, core/knowledge_graph, core/semantic_digest, dev/librarian, knowledge_engine | HIGH |
| inspection | core/knowledge_catalog, core/semantic_digest, dev/librarian, knowledge_engine | HIGH |
| normalization | core/knowledge_catalog, core/semantic_digest, dev/librarian, knowledge_engine | HIGH |
| search | core/knowledge_catalog, dev/librarian, knowledge_engine | HIGH |
| storage | core/knowledge_catalog, core/knowledge_graph, dev/librarian, knowledge_engine | HIGH |

## Module Details

### `core.knowledge_catalog.__init__`

- Path: `core/knowledge_catalog/__init__.py`
- Package: `core/knowledge_catalog`
- Capabilities: catalog
- CLI: no
- Database: no

### `core.knowledge_catalog.backfill`

- Path: `core/knowledge_catalog/backfill.py`
- Package: `core/knowledge_catalog`
- Capabilities: catalog, classification, extraction, storage
- CLI: yes
- Database: yes
- Functions: main

### `core.knowledge_catalog.classifiers.__init__`

- Path: `core/knowledge_catalog/classifiers/__init__.py`
- Package: `core/knowledge_catalog`
- Capabilities: catalog, classification
- CLI: no
- Database: no

### `core.knowledge_catalog.classifiers.keyword_classifier`

- Path: `core/knowledge_catalog/classifiers/keyword_classifier.py`
- Package: `core/knowledge_catalog`
- Capabilities: catalog, classification, extraction, graph
- CLI: no
- Database: no
- Functions: load_keyword_rules, classify_text

### `core.knowledge_catalog.classifiers.subject_assignment`

- Path: `core/knowledge_catalog/classifiers/subject_assignment.py`
- Package: `core/knowledge_catalog`
- Capabilities: catalog, classification, extraction
- CLI: no
- Database: no
- Functions: assign_subject

### `core.knowledge_catalog.cli`

- Path: `core/knowledge_catalog/cli.py`
- Package: `core/knowledge_catalog`
- Capabilities: acquisition, catalog, classification, collections, search, storage
- CLI: yes
- Database: yes
- Functions: cmd_init, cmd_stats, cmd_topics, cmd_sources, cmd_collections_build, cmd_collections_list, cmd_semantic_backfill, cmd_search, cmd_register_file, cmd_register_tree, main

### `core.knowledge_catalog.collections`

- Path: `core/knowledge_catalog/collections.py`
- Package: `core/knowledge_catalog`
- Capabilities: catalog, classification, collections, extraction, graph, normalization, storage
- CLI: no
- Database: yes
- Classes: CollectionCandidate
- Functions: utc_now, humanize, classify_folder, count_assets, discover_collections, upsert_collections, print_collections

### `core.knowledge_catalog.config`

- Path: `core/knowledge_catalog/config.py`
- Package: `core/knowledge_catalog`
- Capabilities: acquisition, catalog, normalization, storage
- CLI: no
- Database: no

### `core.knowledge_catalog.database`

- Path: `core/knowledge_catalog/database.py`
- Package: `core/knowledge_catalog`
- Capabilities: catalog, classification, collections, extraction, inspection, storage
- CLI: no
- Database: yes
- Functions: connect, migrate

### `core.knowledge_catalog.digest`

- Path: `core/knowledge_catalog/digest.py`
- Package: `core/knowledge_catalog`
- Capabilities: catalog, chunking, classification, extraction, graph, normalization
- CLI: no
- Database: no
- Functions: sha256_file, load_keyword_rules, normalize_text, digest_path

### `core.knowledge_catalog.models`

- Path: `core/knowledge_catalog/models.py`
- Package: `core/knowledge_catalog`
- Capabilities: acquisition, catalog, inspection
- CLI: no
- Database: no
- Classes: Source, Topic, Document, FileAsset
- Functions: utc_now

### `core.knowledge_catalog.paths`

- Path: `core/knowledge_catalog/paths.py`
- Package: `core/knowledge_catalog`
- Capabilities: catalog, storage
- CLI: no
- Database: no

### `core.knowledge_catalog.registrar`

- Path: `core/knowledge_catalog/registrar.py`
- Package: `core/knowledge_catalog`
- Capabilities: acquisition, catalog, classification, collections, extraction, inspection, storage
- CLI: no
- Database: yes
- Functions: utc_now, infer_collection_id, register_file, register_tree

### `core.knowledge_catalog.repository`

- Path: `core/knowledge_catalog/repository.py`
- Package: `core/knowledge_catalog`
- Capabilities: acquisition, catalog, inspection, storage
- CLI: no
- Database: yes
- Classes: CatalogRepository
- Functions: upsert_source, upsert_topic, create_document, add_file_asset, link_document_topic, stats

### `core.knowledge_catalog.schema`

- Path: `core/knowledge_catalog/schema.py`
- Package: `core/knowledge_catalog`
- Capabilities: acquisition, catalog, classification, collections, embedding, extraction, inspection
- CLI: no
- Database: yes

### `core.knowledge_catalog.search`

- Path: `core/knowledge_catalog/search.py`
- Package: `core/knowledge_catalog`
- Capabilities: catalog, classification, search, storage
- CLI: no
- Database: yes
- Functions: search_catalog

### `core.knowledge_catalog.seed`

- Path: `core/knowledge_catalog/seed.py`
- Package: `core/knowledge_catalog`
- Capabilities: acquisition, catalog, embedding, extraction, graph, storage
- CLI: no
- Database: no
- Functions: seed_catalog

### `core.knowledge_catalog.service`

- Path: `core/knowledge_catalog/service.py`
- Package: `core/knowledge_catalog`
- Capabilities: acquisition, catalog, inspection, storage
- CLI: no
- Database: yes
- Functions: initialize_catalog, register_file

### `core.knowledge_graph.__init__`

- Path: `core/knowledge_graph/__init__.py`
- Package: `core/knowledge_graph`
- Capabilities: graph
- CLI: no
- Database: no

### `core.knowledge_graph.catalog_mapper`

- Path: `core/knowledge_graph/catalog_mapper.py`
- Package: `core/knowledge_graph`
- Capabilities: catalog, classification, graph
- CLI: no
- Database: no

### `core.knowledge_graph.cli`

- Path: `core/knowledge_graph/cli.py`
- Package: `core/knowledge_graph`
- Capabilities: classification, extraction, graph
- CLI: yes
- Database: no
- Functions: cmd_summary, cmd_gaps, main

### `core.knowledge_graph.coverage`

- Path: `core/knowledge_graph/coverage.py`
- Package: `core/knowledge_graph`
- Capabilities: graph
- CLI: no
- Database: no

### `core.knowledge_graph.gap_analysis`

- Path: `core/knowledge_graph/gap_analysis.py`
- Package: `core/knowledge_graph`
- Capabilities: catalog, classification, extraction, graph, storage
- CLI: no
- Database: yes
- Classes: SubjectCoverage
- Functions: status_from_count, iter_subjects, load_subject_counts, analyze_gaps, summarize, write_reports

### `core.knowledge_graph.graph`

- Path: `core/knowledge_graph/graph.py`
- Package: `core/knowledge_graph`
- Capabilities: graph
- CLI: no
- Database: no

### `core.knowledge_graph.models`

- Path: `core/knowledge_graph/models.py`
- Package: `core/knowledge_graph`
- Capabilities: graph
- CLI: no
- Database: no

### `core.knowledge_graph.ontology`

- Path: `core/knowledge_graph/ontology.py`
- Package: `core/knowledge_graph`
- Capabilities: classification, graph
- CLI: no
- Database: no
- Classes: KnowledgeOntology
- Functions: load_ontology

### `core.knowledge_mapper.__init__`

- Path: `core/knowledge_mapper/__init__.py`
- Package: `core/knowledge_mapper`
- Capabilities: classification
- CLI: no
- Database: no

### `core.knowledge_mapper.cli`

- Path: `core/knowledge_mapper/cli.py`
- Package: `core/knowledge_mapper`
- Capabilities: classification
- CLI: yes
- Database: no

### `core.knowledge_mapper.indexer`

- Path: `core/knowledge_mapper/indexer.py`
- Package: `core/knowledge_mapper`
- Capabilities: classification, collections, extraction
- CLI: no
- Database: no
- Functions: build_subject_index

### `core.knowledge_mapper.mapper`

- Path: `core/knowledge_mapper/mapper.py`
- Package: `core/knowledge_mapper`
- Capabilities: classification
- CLI: no
- Database: no
- Functions: map_path

### `core.knowledge_mapper.models`

- Path: `core/knowledge_mapper/models.py`
- Package: `core/knowledge_mapper`
- Capabilities: classification
- CLI: no
- Database: no

### `core.knowledge_mapper.report`

- Path: `core/knowledge_mapper/report.py`
- Package: `core/knowledge_mapper`
- Capabilities: classification
- CLI: no
- Database: no
- Functions: print_summary

### `core.knowledge_mapper.rules`

- Path: `core/knowledge_mapper/rules.py`
- Package: `core/knowledge_mapper`
- Capabilities: classification
- CLI: no
- Database: no
- Functions: load_rules

### `core.semantic_digest.__init__`

- Path: `core/semantic_digest/__init__.py`
- Package: `core/semantic_digest`
- Capabilities: classification
- CLI: no
- Database: no

### `core.semantic_digest.analyzer`

- Path: `core/semantic_digest/analyzer.py`
- Package: `core/semantic_digest`
- Capabilities: classification, extraction, graph, normalization
- CLI: no
- Database: no
- Functions: load_rules, normalize, analyze_semantics

### `core.semantic_digest.cli`

- Path: `core/semantic_digest/cli.py`
- Package: `core/semantic_digest`
- Capabilities: catalog, classification, inspection
- CLI: yes
- Database: no
- Functions: cmd_inspect, cmd_digest, main

### `core.semantic_digest.inspector`

- Path: `core/semantic_digest/inspector.py`
- Package: `core/semantic_digest`
- Capabilities: catalog, classification, extraction, inspection
- CLI: no
- Database: no
- Classes: DocumentInspection
- Functions: inspect_document

### `core.semantic_digest.pipeline`

- Path: `core/semantic_digest/pipeline.py`
- Package: `core/semantic_digest`
- Capabilities: catalog, classification, extraction, inspection
- CLI: no
- Database: no
- Functions: process_document

### `core.semantic_digest.readers`

- Path: `core/semantic_digest/readers.py`
- Package: `core/semantic_digest`
- Capabilities: catalog, chunking, classification, extraction, inspection
- CLI: no
- Database: no
- Functions: read_text_file, read_pdf, read_document

### `core.semantic_digest.structural`

- Path: `core/semantic_digest/structural.py`
- Package: `core/semantic_digest`
- Capabilities: classification, collections, extraction
- CLI: no
- Database: no
- Functions: clean_line, extract_headings, extract_terms, extract_structure

### `dev.librarian.__init__`

- Path: `dev/librarian/__init__.py`
- Package: `dev/librarian`
- Capabilities: none detected
- CLI: no
- Database: no

### `dev.librarian.acquire_pipeline`

- Path: `dev/librarian/acquire_pipeline.py`
- Package: `dev/librarian`
- Capabilities: acquisition, catalog, extraction, normalization
- CLI: yes
- Database: no
- Functions: process_zip, main

### `dev.librarian.acquisition.__init__`

- Path: `dev/librarian/acquisition/__init__.py`
- Package: `dev/librarian`
- Capabilities: none detected
- CLI: no
- Database: no

### `dev.librarian.acquisition.archive`

- Path: `dev/librarian/acquisition/archive.py`
- Package: `dev/librarian`
- Capabilities: normalization
- CLI: no
- Database: no
- Functions: archive

### `dev.librarian.acquisition.filter`

- Path: `dev/librarian/acquisition/filter.py`
- Package: `dev/librarian`
- Capabilities: acquisition, extraction
- CLI: no
- Database: no
- Functions: should_keep

### `dev.librarian.acquisition.manifest`

- Path: `dev/librarian/acquisition/manifest.py`
- Package: `dev/librarian`
- Capabilities: acquisition, chunking, normalization
- CLI: no
- Database: no
- Functions: sha256_file, append_manifest

### `dev.librarian.acquisition.metadata`

- Path: `dev/librarian/acquisition/metadata.py`
- Package: `dev/librarian`
- Capabilities: extraction, normalization
- CLI: no
- Database: no
- Functions: load_json, extract_course_metadata, write_metadata

### `dev.librarian.acquisition.normalize`

- Path: `dev/librarian/acquisition/normalize.py`
- Package: `dev/librarian`
- Capabilities: acquisition, catalog, classification, extraction, normalization
- CLI: no
- Database: no
- Functions: extract_zip, classify_kind, copy_useful_assets

### `dev.librarian.acquisition.pipeline`

- Path: `dev/librarian/acquisition/pipeline.py`
- Package: `dev/librarian`
- Capabilities: acquisition, extraction, normalization
- CLI: no
- Database: no
- Functions: process

### `dev.librarian.cko.__init__`

- Path: `dev/librarian/cko/__init__.py`
- Package: `dev/librarian`
- Capabilities: cko
- CLI: no
- Database: no

### `dev.librarian.cko.database`

- Path: `dev/librarian/cko/database.py`
- Package: `dev/librarian`
- Capabilities: acquisition, cko, extraction, inspection, storage
- CLI: no
- Database: yes
- Functions: connect, migrate

### `dev.librarian.cko.mit_cko_builder`

- Path: `dev/librarian/cko/mit_cko_builder.py`
- Package: `dev/librarian`
- Capabilities: acquisition, chunking, cko, extraction, inspection, normalization, search, storage
- CLI: yes
- Database: yes
- Functions: utc_now, sha256_file, safe_name, load_json, guess_type, find_course_root, extract_title, collect_static_pdfs, find_pdf_for_resource, add_cko, add_representation, materialize_representation, build_course, main

### `dev.librarian.discover`

- Path: `dev/librarian/discover.py`
- Package: `dev/librarian`
- Capabilities: acquisition, search
- CLI: yes
- Database: no
- Functions: main

### `dev.librarian.discovery.__init__`

- Path: `dev/librarian/discovery/__init__.py`
- Package: `dev/librarian`
- Capabilities: none detected
- CLI: no
- Database: no

### `dev.librarian.discovery.engine`

- Path: `dev/librarian/discovery/engine.py`
- Package: `dev/librarian`
- Capabilities: acquisition, extraction, graph, normalization, search
- CLI: no
- Database: no
- Functions: normalize_topic, human_topic, slugify, load_sources, source_matches_topic, score_candidate, discover, write_discovery_plan

### `dev.librarian.discovery.models`

- Path: `dev/librarian/discovery/models.py`
- Package: `dev/librarian`
- Capabilities: acquisition, search
- CLI: no
- Database: no
- Classes: TrustedSource, DiscoveryCandidate
- Functions: utc_now, to_dict

### `dev.librarian.integration.__init__`

- Path: `dev/librarian/integration/__init__.py`
- Package: `dev/librarian`
- Capabilities: none detected
- CLI: no
- Database: no

### `dev.librarian.inventory.__init__`

- Path: `dev/librarian/inventory/__init__.py`
- Package: `dev/librarian`
- Capabilities: none detected
- CLI: no
- Database: no

### `dev.librarian.inventory.inventory`

- Path: `dev/librarian/inventory/inventory.py`
- Package: `dev/librarian`
- Capabilities: catalog, collections, extraction
- CLI: no
- Database: no

### `dev.librarian.librarian`

- Path: `dev/librarian/librarian.py`
- Package: `dev/librarian`
- Capabilities: catalog
- CLI: yes
- Database: no
- Functions: register

### `dev.librarian.mit_miner`

- Path: `dev/librarian/mit_miner.py`
- Package: `dev/librarian`
- Capabilities: acquisition, chunking, extraction, normalization, search
- CLI: yes
- Database: no
- Functions: sha256, search, mine_course, download, main

### `dev.librarian.mit_targeted_miner`

- Path: `dev/librarian/mit_targeted_miner.py`
- Package: `dev/librarian`
- Capabilities: acquisition, chunking, extraction, inspection, normalization
- CLI: yes
- Database: no
- Classes: Links
- Functions: fetch, text_from_html, sha256_file, safe_name, write_manifest, download, mine_ocw_course_zip, mine_mit_press_books, main, handle_starttag

### `dev.librarian.pdf_hunter`

- Path: `dev/librarian/pdf_hunter.py`
- Package: `dev/librarian`
- Capabilities: acquisition, chunking, collections, extraction, normalization, search, storage
- CLI: yes
- Database: no
- Classes: LinkParser
- Functions: sha256_file, fetch, safe_filename, same_domain, robots_allowed, crawl, main, handle_starttag

### `dev.librarian.run_pipeline`

- Path: `dev/librarian/run_pipeline.py`
- Package: `dev/librarian`
- Capabilities: acquisition, normalization
- CLI: no
- Database: no

### `knowledge_engine.__init__`

- Path: `knowledge_engine/__init__.py`
- Package: `knowledge_engine`
- Capabilities: search
- CLI: no
- Database: no

### `knowledge_engine.catalog`

- Path: `knowledge_engine/catalog.py`
- Package: `knowledge_engine`
- Capabilities: acquisition, catalog, extraction, inspection, normalization, storage
- CLI: no
- Database: yes
- Classes: KnowledgeCatalog
- Functions: connect, initialize, upsert_document, upsert_inspection, summary, duplicate_groups, replace_structure, structure_summary

### `knowledge_engine.catalog.__init__`

- Path: `knowledge_engine/catalog/__init__.py`
- Package: `knowledge_engine`
- Capabilities: catalog
- CLI: no
- Database: no

### `knowledge_engine.chunking.__init__`

- Path: `knowledge_engine/chunking/__init__.py`
- Package: `knowledge_engine`
- Capabilities: chunking
- CLI: no
- Database: no

### `knowledge_engine.chunking.chunker`

- Path: `knowledge_engine/chunking/chunker.py`
- Package: `knowledge_engine`
- Capabilities: chunking
- CLI: no
- Database: no

### `knowledge_engine.cli`

- Path: `knowledge_engine/cli.py`
- Package: `knowledge_engine`
- Capabilities: acquisition, catalog, extraction, inspection, storage
- CLI: yes
- Database: no
- Functions: section, main

### `knowledge_engine.collections.__init__`

- Path: `knowledge_engine/collections/__init__.py`
- Package: `knowledge_engine`
- Capabilities: collections
- CLI: no
- Database: no

### `knowledge_engine.collections.models`

- Path: `knowledge_engine/collections/models.py`
- Package: `knowledge_engine`
- Capabilities: collections
- CLI: no
- Database: no

### `knowledge_engine.collections.store`

- Path: `knowledge_engine/collections/store.py`
- Package: `knowledge_engine`
- Capabilities: collections, storage
- CLI: no
- Database: no

### `knowledge_engine.concepts.__init__`

- Path: `knowledge_engine/concepts/__init__.py`
- Package: `knowledge_engine`
- Capabilities: classification
- CLI: no
- Database: no

### `knowledge_engine.constants`

- Path: `knowledge_engine/constants.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no

### `knowledge_engine.discovery.__init__`

- Path: `knowledge_engine/discovery/__init__.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no

### `knowledge_engine.discovery.scanner`

- Path: `knowledge_engine/discovery/scanner.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no
- Functions: discover_files

### `knowledge_engine.document`

- Path: `knowledge_engine/document.py`
- Package: `knowledge_engine`
- Capabilities: catalog
- CLI: no
- Database: no
- Classes: DocumentRecord
- Functions: relative_path

### `knowledge_engine.embeddings.__init__`

- Path: `knowledge_engine/embeddings/__init__.py`
- Package: `knowledge_engine`
- Capabilities: embedding
- CLI: no
- Database: no

### `knowledge_engine.embeddings.engine`

- Path: `knowledge_engine/embeddings/engine.py`
- Package: `knowledge_engine`
- Capabilities: embedding
- CLI: no
- Database: no

### `knowledge_engine.extraction.__init__`

- Path: `knowledge_engine/extraction/__init__.py`
- Package: `knowledge_engine`
- Capabilities: extraction
- CLI: no
- Database: no

### `knowledge_engine.extraction.extractors.__init__`

- Path: `knowledge_engine/extraction/extractors/__init__.py`
- Package: `knowledge_engine`
- Capabilities: extraction
- CLI: no
- Database: no

### `knowledge_engine.extraction.extractors.base`

- Path: `knowledge_engine/extraction/extractors/base.py`
- Package: `knowledge_engine`
- Capabilities: extraction
- CLI: no
- Database: no
- Classes: BaseExtractor
- Functions: supports, extract

### `knowledge_engine.extraction.extractors.pdf`

- Path: `knowledge_engine/extraction/extractors/pdf.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction
- CLI: no
- Database: no
- Classes: PDFExtractor
- Functions: supports, extract

### `knowledge_engine.index.__init__`

- Path: `knowledge_engine/index/__init__.py`
- Package: `knowledge_engine`
- Capabilities: search, storage
- CLI: no
- Database: no

### `knowledge_engine.index.builder`

- Path: `knowledge_engine/index/builder.py`
- Package: `knowledge_engine`
- Capabilities: catalog, classification, inspection, normalization, storage
- CLI: no
- Database: yes
- Classes: KnowledgeIndexBuilder
- Functions: build

### `knowledge_engine.index.models`

- Path: `knowledge_engine/index/models.py`
- Package: `knowledge_engine`
- Capabilities: catalog, classification
- CLI: no
- Database: no
- Classes: IndexRecord

### `knowledge_engine.index.search`

- Path: `knowledge_engine/index/search.py`
- Package: `knowledge_engine`
- Capabilities: catalog, classification, search, storage
- CLI: no
- Database: yes
- Classes: KnowledgeIndexSearch
- Functions: search

### `knowledge_engine.index.statistics`

- Path: `knowledge_engine/index/statistics.py`
- Package: `knowledge_engine`
- Capabilities: storage
- CLI: no
- Database: yes
- Classes: KnowledgeIndexStatistics
- Functions: top_categories

### `knowledge_engine.index.store`

- Path: `knowledge_engine/index/store.py`
- Package: `knowledge_engine`
- Capabilities: catalog, classification, storage
- CLI: no
- Database: yes
- Classes: KnowledgeIndexStore
- Functions: upsert, summary

### `knowledge_engine.inspection.__init__`

- Path: `knowledge_engine/inspection/__init__.py`
- Package: `knowledge_engine`
- Capabilities: inspection
- CLI: no
- Database: no

### `knowledge_engine.inspectors.__init__`

- Path: `knowledge_engine/inspectors/__init__.py`
- Package: `knowledge_engine`
- Capabilities: inspection
- CLI: no
- Database: no

### `knowledge_engine.inspectors.base`

- Path: `knowledge_engine/inspectors/base.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction, inspection, normalization
- CLI: no
- Database: no
- Classes: BaseInspector
- Functions: inspect, extract_text

### `knowledge_engine.inspectors.docx`

- Path: `knowledge_engine/inspectors/docx.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction, graph, inspection
- CLI: no
- Database: no
- Classes: DocxInspector
- Functions: inspect

### `knowledge_engine.inspectors.epub`

- Path: `knowledge_engine/inspectors/epub.py`
- Package: `knowledge_engine`
- Capabilities: extraction, inspection, normalization
- CLI: no
- Database: no
- Classes: EpubInspector
- Functions: inspect

### `knowledge_engine.inspectors.html`

- Path: `knowledge_engine/inspectors/html.py`
- Package: `knowledge_engine`
- Capabilities: extraction, inspection
- CLI: no
- Database: no
- Classes: HtmlInspector
- Functions: inspect

### `knowledge_engine.inspectors.image`

- Path: `knowledge_engine/inspectors/image.py`
- Package: `knowledge_engine`
- Capabilities: inspection
- CLI: no
- Database: no
- Classes: ImageInspector
- Functions: inspect

### `knowledge_engine.inspectors.markdown`

- Path: `knowledge_engine/inspectors/markdown.py`
- Package: `knowledge_engine`
- Capabilities: extraction, inspection
- CLI: no
- Database: no
- Classes: MarkdownInspector

### `knowledge_engine.inspectors.pdf`

- Path: `knowledge_engine/inspectors/pdf.py`
- Package: `knowledge_engine`
- Capabilities: extraction, inspection, normalization, search
- CLI: no
- Database: no
- Classes: PDFInspector
- Functions: inspect

### `knowledge_engine.inspectors.registry`

- Path: `knowledge_engine/inspectors/registry.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction, inspection
- CLI: no
- Database: no
- Classes: InspectorRegistry
- Functions: register, get

### `knowledge_engine.inspectors.text`

- Path: `knowledge_engine/inspectors/text.py`
- Package: `knowledge_engine`
- Capabilities: extraction, inspection
- CLI: no
- Database: no
- Classes: TextInspector
- Functions: inspect

### `knowledge_engine.inspectors.zim`

- Path: `knowledge_engine/inspectors/zim.py`
- Package: `knowledge_engine`
- Capabilities: extraction, inspection
- CLI: no
- Database: no
- Classes: ZimInspector
- Functions: inspect

### `knowledge_engine.library.__init__`

- Path: `knowledge_engine/library/__init__.py`
- Package: `knowledge_engine`
- Capabilities: catalog, storage
- CLI: no
- Database: no

### `knowledge_engine.library.builder`

- Path: `knowledge_engine/library/builder.py`
- Package: `knowledge_engine`
- Capabilities: acquisition, catalog, classification, inspection, normalization, storage
- CLI: no
- Database: yes
- Classes: LibraryCatalogBuilder
- Functions: build

### `knowledge_engine.library.models`

- Path: `knowledge_engine/library/models.py`
- Package: `knowledge_engine`
- Capabilities: acquisition, catalog, classification
- CLI: no
- Database: no
- Classes: LibraryRecord

### `knowledge_engine.library.store`

- Path: `knowledge_engine/library/store.py`
- Package: `knowledge_engine`
- Capabilities: acquisition, catalog, classification, storage
- CLI: no
- Database: yes
- Classes: LibraryCatalogStore
- Functions: upsert, summary

### `knowledge_engine.metadata.__init__`

- Path: `knowledge_engine/metadata/__init__.py`
- Package: `knowledge_engine`
- Capabilities: normalization
- CLI: no
- Database: no

### `knowledge_engine.metadata.fingerprints`

- Path: `knowledge_engine/metadata/fingerprints.py`
- Package: `knowledge_engine`
- Capabilities: chunking, normalization
- CLI: no
- Database: no
- Functions: sha256_file

### `knowledge_engine.pages.__init__`

- Path: `knowledge_engine/pages/__init__.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no

### `knowledge_engine.pages.models`

- Path: `knowledge_engine/pages/models.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction
- CLI: no
- Database: no
- Classes: Page

### `knowledge_engine.pages.store`

- Path: `knowledge_engine/pages/store.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction, storage
- CLI: no
- Database: yes
- Classes: PageStore
- Functions: replace_pages

### `knowledge_engine.pipeline`

- Path: `knowledge_engine/pipeline.py`
- Package: `knowledge_engine`
- Capabilities: catalog, inspection
- CLI: no
- Database: no
- Functions: run_inventory

### `knowledge_engine.processing.__init__`

- Path: `knowledge_engine/processing/__init__.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no

### `knowledge_engine.processing.catalog_stage`

- Path: `knowledge_engine/processing/catalog_stage.py`
- Package: `knowledge_engine`
- Capabilities: catalog, normalization, storage
- CLI: no
- Database: no
- Classes: CatalogStage
- Functions: category_from_path, build_record, run

### `knowledge_engine.processing.chunk_stage`

- Path: `knowledge_engine/processing/chunk_stage.py`
- Package: `knowledge_engine`
- Capabilities: chunking
- CLI: no
- Database: no

### `knowledge_engine.processing.concept_stage`

- Path: `knowledge_engine/processing/concept_stage.py`
- Package: `knowledge_engine`
- Capabilities: classification
- CLI: no
- Database: no

### `knowledge_engine.processing.discover`

- Path: `knowledge_engine/processing/discover.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no

### `knowledge_engine.processing.extract_stage`

- Path: `knowledge_engine/processing/extract_stage.py`
- Package: `knowledge_engine`
- Capabilities: extraction
- CLI: no
- Database: no

### `knowledge_engine.processing.extract_text_stage`

- Path: `knowledge_engine/processing/extract_text_stage.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction, storage
- CLI: no
- Database: no
- Classes: ExtractTextStage
- Functions: run

### `knowledge_engine.processing.inspect_stage`

- Path: `knowledge_engine/processing/inspect_stage.py`
- Package: `knowledge_engine`
- Capabilities: catalog, inspection, normalization, storage
- CLI: no
- Database: no
- Classes: InspectStage
- Functions: run

### `knowledge_engine.processing.processor`

- Path: `knowledge_engine/processing/processor.py`
- Package: `knowledge_engine`
- Capabilities: catalog, inspection, storage
- CLI: no
- Database: no
- Classes: ProcessingEngine
- Functions: run_foundation

### `knowledge_engine.processing.retrieve_stage`

- Path: `knowledge_engine/processing/retrieve_stage.py`
- Package: `knowledge_engine`
- Capabilities: search
- CLI: no
- Database: no

### `knowledge_engine.processing.structure_stage`

- Path: `knowledge_engine/processing/structure_stage.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction, storage
- CLI: no
- Database: no
- Classes: StructureStage
- Functions: run

### `knowledge_engine.providers.__init__`

- Path: `knowledge_engine/providers/__init__.py`
- Package: `knowledge_engine`
- Capabilities: acquisition
- CLI: no
- Database: no

### `knowledge_engine.providers.base`

- Path: `knowledge_engine/providers/base.py`
- Package: `knowledge_engine`
- Capabilities: acquisition
- CLI: no
- Database: no

### `knowledge_engine.providers.faa`

- Path: `knowledge_engine/providers/faa.py`
- Package: `knowledge_engine`
- Capabilities: acquisition
- CLI: no
- Database: no

### `knowledge_engine.providers.local`

- Path: `knowledge_engine/providers/local.py`
- Package: `knowledge_engine`
- Capabilities: acquisition
- CLI: no
- Database: no

### `knowledge_engine.providers.nasa`

- Path: `knowledge_engine/providers/nasa.py`
- Package: `knowledge_engine`
- Capabilities: acquisition
- CLI: no
- Database: no

### `knowledge_engine.providers.noaa`

- Path: `knowledge_engine/providers/noaa.py`
- Package: `knowledge_engine`
- Capabilities: acquisition
- CLI: no
- Database: no

### `knowledge_engine.providers.provider`

- Path: `knowledge_engine/providers/provider.py`
- Package: `knowledge_engine`
- Capabilities: acquisition
- CLI: no
- Database: no

### `knowledge_engine.providers.registry`

- Path: `knowledge_engine/providers/registry.py`
- Package: `knowledge_engine`
- Capabilities: acquisition
- CLI: no
- Database: no

### `knowledge_engine.providers.us_army`

- Path: `knowledge_engine/providers/us_army.py`
- Package: `knowledge_engine`
- Capabilities: acquisition
- CLI: no
- Database: no

### `knowledge_engine.providers.who`

- Path: `knowledge_engine/providers/who.py`
- Package: `knowledge_engine`
- Capabilities: acquisition
- CLI: no
- Database: no

### `knowledge_engine.queue.__init__`

- Path: `knowledge_engine/queue/__init__.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no

### `knowledge_engine.queue.builder`

- Path: `knowledge_engine/queue/builder.py`
- Package: `knowledge_engine`
- Capabilities: catalog
- CLI: no
- Database: no
- Classes: ProcessingQueueBuilder
- Functions: build

### `knowledge_engine.queue.models`

- Path: `knowledge_engine/queue/models.py`
- Package: `knowledge_engine`
- Capabilities: catalog
- CLI: no
- Database: no
- Classes: QueueItem

### `knowledge_engine.queue.priorities`

- Path: `knowledge_engine/queue/priorities.py`
- Package: `knowledge_engine`
- Capabilities: graph, normalization
- CLI: no
- Database: no

### `knowledge_engine.readers`

- Path: `knowledge_engine/readers.py`
- Package: `knowledge_engine`
- Capabilities: extraction
- CLI: no
- Database: no
- Functions: read_pdf_pages

### `knowledge_engine.reports.__init__`

- Path: `knowledge_engine/reports/__init__.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no

### `knowledge_engine.reports.duplicates`

- Path: `knowledge_engine/reports/duplicates.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no
- Functions: write_duplicates_csv, write_duplicates_markdown

### `knowledge_engine.retrieval.__init__`

- Path: `knowledge_engine/retrieval/__init__.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no

### `knowledge_engine.search.__init__`

- Path: `knowledge_engine/search/__init__.py`
- Package: `knowledge_engine`
- Capabilities: search
- CLI: no
- Database: no

### `knowledge_engine.search.local_search`

- Path: `knowledge_engine/search/local_search.py`
- Package: `knowledge_engine`
- Capabilities: search
- CLI: no
- Database: no

### `knowledge_engine.search.retrieval`

- Path: `knowledge_engine/search/retrieval.py`
- Package: `knowledge_engine`
- Capabilities: search
- CLI: no
- Database: no

### `knowledge_engine.storage.__init__`

- Path: `knowledge_engine/storage/__init__.py`
- Package: `knowledge_engine`
- Capabilities: storage
- CLI: no
- Database: no

### `knowledge_engine.storage.catalog_store`

- Path: `knowledge_engine/storage/catalog_store.py`
- Package: `knowledge_engine`
- Capabilities: catalog, storage
- CLI: no
- Database: yes
- Classes: CatalogStore
- Functions: upsert_document, summary

### `knowledge_engine.storage.chunk_store`

- Path: `knowledge_engine/storage/chunk_store.py`
- Package: `knowledge_engine`
- Capabilities: chunking, storage
- CLI: no
- Database: no

### `knowledge_engine.storage.concept_store`

- Path: `knowledge_engine/storage/concept_store.py`
- Package: `knowledge_engine`
- Capabilities: classification, storage
- CLI: no
- Database: no

### `knowledge_engine.storage.database`

- Path: `knowledge_engine/storage/database.py`
- Package: `knowledge_engine`
- Capabilities: acquisition, catalog, chunking, classification, extraction, inspection, normalization, storage
- CLI: no
- Database: yes
- Classes: KnowledgeDatabase
- Functions: connect, initialize

### `knowledge_engine.storage.inspection_store`

- Path: `knowledge_engine/storage/inspection_store.py`
- Package: `knowledge_engine`
- Capabilities: catalog, inspection, normalization, storage
- CLI: no
- Database: yes
- Classes: InspectionStore
- Functions: upsert

### `knowledge_engine.storage.page_store`

- Path: `knowledge_engine/storage/page_store.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction, search, storage
- CLI: no
- Database: yes
- Classes: PageStore
- Functions: replace_pages, search

### `knowledge_engine.storage.structure_store`

- Path: `knowledge_engine/storage/structure_store.py`
- Package: `knowledge_engine`
- Capabilities: acquisition, catalog, storage
- CLI: no
- Database: yes
- Classes: StructureStore
- Functions: replace, summary

### `knowledge_engine.storage.text_store`

- Path: `knowledge_engine/storage/text_store.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction, storage
- CLI: no
- Database: yes
- Classes: TextStore
- Functions: upsert

### `knowledge_engine.structure.__init__`

- Path: `knowledge_engine/structure/__init__.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no

### `knowledge_engine.structure.base`

- Path: `knowledge_engine/structure/base.py`
- Package: `knowledge_engine`
- Capabilities: acquisition, catalog
- CLI: no
- Database: no
- Classes: StructureNode

### `knowledge_engine.structure.pdf`

- Path: `knowledge_engine/structure/pdf.py`
- Package: `knowledge_engine`
- Capabilities: acquisition, catalog, extraction
- CLI: no
- Database: no
- Classes: PDFStructureExtractor
- Functions: extract

### `knowledge_engine.structure.registry`

- Path: `knowledge_engine/structure/registry.py`
- Package: `knowledge_engine`
- Capabilities: catalog, extraction
- CLI: no
- Database: no
- Classes: StructureRegistry
- Functions: register, get

### `knowledge_engine.tests.__init__`

- Path: `knowledge_engine/tests/__init__.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no

### `knowledge_engine.types`

- Path: `knowledge_engine/types.py`
- Package: `knowledge_engine`
- Capabilities: none detected
- CLI: no
- Database: no
