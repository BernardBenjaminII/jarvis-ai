# JARVIS Knowledge Architecture Map

Generated from source code. This report is for architecture decisions, not runtime behavior.

## Package Summary

| Package | Modules | Classes | Functions | Imports In | Imports Out | Capabilities |
|---|---:|---:|---:|---:|---:|---|
| core/knowledge_catalog | 18 | 6 | 43 | 32 | 71 | acquisition, catalog, chunking, classification, discovery, embedding, extraction, graph, inspection, normalization, reading, search, storage |
| core/knowledge_graph | 8 | 2 | 10 | 3 | 14 | catalog, classification, graph, reading, storage |
| core/knowledge_mapper | 7 | 0 | 4 | 6 | 13 | classification, reading |
| core/semantic_digest | 7 | 1 | 15 | 8 | 29 | catalog, chunking, classification, extraction, graph, inspection, normalization, reading |
| dev/librarian | 24 | 4 | 64 | 7 | 91 | acquisition, catalog, chunking, cko, classification, discovery, extraction, graph, inspection, normalization, reading, search, storage |
| knowledge_engine | 95 | 40 | 62 | 64 | 103 | catalog, chunking, classification, discovery, embedding, extraction, graph, inspection, normalization, reading, search, storage |

## Capability Ownership Decision Draft

| Capability | Detected Owners | Proposed Canonical Owner | Action |
|---|---|---|---|
| acquisition | core/knowledge_catalog, dev/librarian | dev/librarian | KEEP canonical; adapt/archive duplicates |
| catalog | core/knowledge_catalog, core/knowledge_graph, core/semantic_digest, dev/librarian, knowledge_engine | core/knowledge_catalog | KEEP canonical; adapt/archive duplicates |
| chunking | core/knowledge_catalog, core/semantic_digest, dev/librarian, knowledge_engine | knowledge_engine | KEEP canonical; adapt/archive duplicates |
| cko | dev/librarian | dev/librarian | KEEP |
| classification | core/knowledge_catalog, core/knowledge_graph, core/knowledge_mapper, core/semantic_digest, dev/librarian, knowledge_engine | core/knowledge_catalog | KEEP canonical; adapt/archive duplicates |
| discovery | core/knowledge_catalog, dev/librarian, knowledge_engine | dev/librarian | KEEP canonical; adapt/archive duplicates |
| embedding | core/knowledge_catalog, knowledge_engine | knowledge_engine | KEEP canonical; adapt/archive duplicates |
| extraction | core/knowledge_catalog, core/semantic_digest, dev/librarian, knowledge_engine | knowledge_engine | KEEP canonical; adapt/archive duplicates |
| graph | core/knowledge_catalog, core/knowledge_graph, core/semantic_digest, dev/librarian, knowledge_engine | core/knowledge_graph | KEEP canonical; adapt/archive duplicates |
| inspection | core/knowledge_catalog, core/semantic_digest, dev/librarian, knowledge_engine | knowledge_engine | KEEP canonical; adapt/archive duplicates |
| normalization | core/knowledge_catalog, core/semantic_digest, dev/librarian, knowledge_engine | dev/librarian | KEEP canonical; adapt/archive duplicates |
| reading | core/knowledge_catalog, core/knowledge_graph, core/knowledge_mapper, core/semantic_digest, dev/librarian, knowledge_engine | knowledge_engine | KEEP canonical; adapt/archive duplicates |
| search | core/knowledge_catalog, dev/librarian, knowledge_engine | core/knowledge_catalog | KEEP canonical; adapt/archive duplicates |
| storage | core/knowledge_catalog, core/knowledge_graph, dev/librarian, knowledge_engine | core/knowledge_catalog | KEEP canonical; adapt/archive duplicates |

## Most Connected Modules

| Module | Package | Imported By | Imports | Capabilities |
|---|---|---:|---:|---|
| `dev.librarian.pdf_hunter` | dev/librarian | 0 | 12 | acquisition, chunking, normalization, reading, search, storage |
| `knowledge_engine.processing.processor` | knowledge_engine | 2 | 9 | catalog, extraction, inspection, storage |
| `core.knowledge_catalog.cli` | core/knowledge_catalog | 0 | 11 | catalog, classification, discovery, search, storage |
| `core.knowledge_catalog.database` | core/knowledge_catalog | 6 | 5 | catalog, classification, extraction, inspection, reading, storage |
| `dev.librarian.cko.mit_cko_builder` | dev/librarian | 0 | 11 | acquisition, chunking, cko, discovery, extraction, inspection, normalization, reading, search, storage |
| `dev.librarian.mit_targeted_miner` | dev/librarian | 0 | 11 | acquisition, chunking, discovery, extraction, inspection, normalization, reading |
| `knowledge_engine.inspectors.registry` | knowledge_engine | 1 | 9 | catalog, inspection, reading |
| `core.knowledge_catalog.collections` | core/knowledge_catalog | 1 | 8 | catalog, classification, discovery, graph, normalization, reading, storage |
| `core.knowledge_catalog.registrar` | core/knowledge_catalog | 2 | 6 | catalog, classification, discovery, extraction, inspection, reading, storage |
| `core.knowledge_graph.gap_analysis` | core/knowledge_graph | 1 | 7 | catalog, classification, graph, reading, storage |
| `core.semantic_digest.pipeline` | core/semantic_digest | 2 | 6 | catalog, classification, extraction, inspection, reading |
| `dev.librarian.acquisition.normalize` | dev/librarian | 1 | 7 | catalog, classification, discovery, extraction, normalization, reading |
| `dev.librarian.mit_miner` | dev/librarian | 0 | 8 | acquisition, chunking, normalization, reading, search |
| `core.knowledge_catalog.backfill` | core/knowledge_catalog | 1 | 6 | catalog, classification, reading, storage |
| `core.knowledge_catalog.config` | core/knowledge_catalog | 6 | 1 | acquisition, catalog, extraction, normalization, storage |
| `core.knowledge_catalog.models` | core/knowledge_catalog | 3 | 4 | catalog, discovery, inspection |
| `core.knowledge_catalog.service` | core/knowledge_catalog | 1 | 6 | catalog, discovery, inspection, storage |
| `core.semantic_digest.readers` | core/semantic_digest | 1 | 6 | catalog, chunking, classification, extraction, inspection, reading |
| `knowledge_engine.document` | knowledge_engine | 3 | 3 | catalog |
| `knowledge_engine.processing.catalog_stage` | knowledge_engine | 2 | 4 | catalog, discovery, extraction, storage |
| `core.knowledge_catalog.classifiers.subject_assignment` | core/knowledge_catalog | 2 | 4 | catalog, classification, reading |
| `core.knowledge_catalog.digest` | core/knowledge_catalog | 1 | 5 | catalog, chunking, classification, graph, normalization, reading |
| `core.knowledge_catalog.repository` | core/knowledge_catalog | 3 | 3 | catalog, discovery, inspection, storage |
| `core.knowledge_catalog.search` | core/knowledge_catalog | 1 | 5 | catalog, classification, search, storage |
| `core.semantic_digest.analyzer` | core/semantic_digest | 1 | 5 | classification, extraction, graph, normalization, reading |
| `core.semantic_digest.inspector` | core/semantic_digest | 3 | 3 | catalog, classification, inspection, reading |
| `dev.librarian.discovery.engine` | dev/librarian | 1 | 5 | acquisition, discovery, graph, normalization, reading, search |
| `knowledge_engine.index.__init__` | knowledge_engine | 1 | 4 | search, storage |
| `knowledge_engine.structure.base` | knowledge_engine | 3 | 2 | catalog, discovery, extraction |
| `knowledge_engine.structure.pdf` | knowledge_engine | 2 | 3 | catalog, discovery, extraction, reading |
| `core.knowledge_graph.ontology` | core/knowledge_graph | 2 | 3 | classification, graph |
| `core.knowledge_mapper.mapper` | core/knowledge_mapper | 3 | 2 | classification |
| `core.semantic_digest.cli` | core/semantic_digest | 0 | 5 | catalog, classification, inspection |
| `core.semantic_digest.structural` | core/semantic_digest | 1 | 4 | classification, extraction, reading |
| `dev.librarian.acquisition.manifest` | dev/librarian | 1 | 4 | chunking, discovery, normalization |
| `dev.librarian.librarian` | dev/librarian | 0 | 5 | catalog |
| `knowledge_engine.index.builder` | knowledge_engine | 2 | 2 | catalog, classification, extraction, inspection, storage |
| `knowledge_engine.index.models` | knowledge_engine | 3 | 1 | catalog, classification, extraction |
| `knowledge_engine.inspectors.base` | knowledge_engine | 1 | 3 | catalog, extraction, inspection, reading |
| `knowledge_engine.inspectors.docx` | knowledge_engine | 1 | 3 | catalog, graph, inspection, reading |

## Duplicate-Risk Modules

Modules below participate in capabilities with multiple detected owners.

### `core.knowledge_catalog.__init__`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/__init__.py`
- Duplicate-risk capabilities: catalog

### `core.knowledge_catalog.backfill`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/backfill.py`
- Duplicate-risk capabilities: catalog, classification, reading, storage
- Functions: main

### `core.knowledge_catalog.classifiers.__init__`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/classifiers/__init__.py`
- Duplicate-risk capabilities: catalog, classification

### `core.knowledge_catalog.classifiers.keyword_classifier`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/classifiers/keyword_classifier.py`
- Duplicate-risk capabilities: catalog, classification, graph, reading
- Functions: load_keyword_rules, classify_text

### `core.knowledge_catalog.classifiers.subject_assignment`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/classifiers/subject_assignment.py`
- Duplicate-risk capabilities: catalog, classification, reading
- Functions: assign_subject

### `core.knowledge_catalog.cli`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/cli.py`
- Duplicate-risk capabilities: catalog, classification, discovery, search, storage
- Functions: cmd_init, cmd_stats, cmd_topics, cmd_sources, cmd_collections_build, cmd_collections_list, cmd_semantic_backfill, cmd_search, cmd_register_file, cmd_register_tree, main

### `core.knowledge_catalog.collections`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/collections.py`
- Duplicate-risk capabilities: catalog, classification, discovery, graph, normalization, reading, storage
- Classes: CollectionCandidate
- Functions: utc_now, humanize, classify_folder, count_assets, discover_collections, upsert_collections, print_collections

### `core.knowledge_catalog.config`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/config.py`
- Duplicate-risk capabilities: acquisition, catalog, extraction, normalization, storage

### `core.knowledge_catalog.database`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/database.py`
- Duplicate-risk capabilities: catalog, classification, extraction, inspection, reading, storage
- Functions: connect, migrate

### `core.knowledge_catalog.digest`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/digest.py`
- Duplicate-risk capabilities: catalog, chunking, classification, graph, normalization, reading
- Functions: sha256_file, load_keyword_rules, normalize_text, digest_path

### `core.knowledge_catalog.models`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/models.py`
- Duplicate-risk capabilities: catalog, discovery, inspection
- Classes: Source, Topic, Document, FileAsset
- Functions: utc_now

### `core.knowledge_catalog.paths`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/paths.py`
- Duplicate-risk capabilities: catalog, storage

### `core.knowledge_catalog.registrar`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/registrar.py`
- Duplicate-risk capabilities: catalog, classification, discovery, extraction, inspection, reading, storage
- Functions: utc_now, infer_collection_id, register_file, register_tree

### `core.knowledge_catalog.repository`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/repository.py`
- Duplicate-risk capabilities: catalog, discovery, inspection, storage
- Classes: CatalogRepository
- Functions: upsert_source, upsert_topic, create_document, add_file_asset, link_document_topic, stats

### `core.knowledge_catalog.schema`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/schema.py`
- Duplicate-risk capabilities: catalog, classification, discovery, embedding, inspection, reading

### `core.knowledge_catalog.search`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/search.py`
- Duplicate-risk capabilities: catalog, classification, search, storage
- Functions: search_catalog

### `core.knowledge_catalog.seed`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/seed.py`
- Duplicate-risk capabilities: catalog, discovery, embedding, graph, reading, storage
- Functions: seed_catalog

### `core.knowledge_catalog.service`
- Package: `core/knowledge_catalog`
- Path: `core/knowledge_catalog/service.py`
- Duplicate-risk capabilities: catalog, discovery, inspection, storage
- Functions: initialize_catalog, register_file

### `core.knowledge_graph.__init__`
- Package: `core/knowledge_graph`
- Path: `core/knowledge_graph/__init__.py`
- Duplicate-risk capabilities: graph

### `core.knowledge_graph.catalog_mapper`
- Package: `core/knowledge_graph`
- Path: `core/knowledge_graph/catalog_mapper.py`
- Duplicate-risk capabilities: catalog, classification, graph

### `core.knowledge_graph.cli`
- Package: `core/knowledge_graph`
- Path: `core/knowledge_graph/cli.py`
- Duplicate-risk capabilities: classification, graph, reading
- Functions: cmd_summary, cmd_gaps, main

### `core.knowledge_graph.coverage`
- Package: `core/knowledge_graph`
- Path: `core/knowledge_graph/coverage.py`
- Duplicate-risk capabilities: graph

### `core.knowledge_graph.gap_analysis`
- Package: `core/knowledge_graph`
- Path: `core/knowledge_graph/gap_analysis.py`
- Duplicate-risk capabilities: catalog, classification, graph, reading, storage
- Classes: SubjectCoverage
- Functions: status_from_count, iter_subjects, load_subject_counts, analyze_gaps, summarize, write_reports

### `core.knowledge_graph.graph`
- Package: `core/knowledge_graph`
- Path: `core/knowledge_graph/graph.py`
- Duplicate-risk capabilities: graph

### `core.knowledge_graph.models`
- Package: `core/knowledge_graph`
- Path: `core/knowledge_graph/models.py`
- Duplicate-risk capabilities: graph

### `core.knowledge_graph.ontology`
- Package: `core/knowledge_graph`
- Path: `core/knowledge_graph/ontology.py`
- Duplicate-risk capabilities: classification, graph
- Classes: KnowledgeOntology
- Functions: load_ontology

### `core.knowledge_mapper.__init__`
- Package: `core/knowledge_mapper`
- Path: `core/knowledge_mapper/__init__.py`
- Duplicate-risk capabilities: classification

### `core.knowledge_mapper.cli`
- Package: `core/knowledge_mapper`
- Path: `core/knowledge_mapper/cli.py`
- Duplicate-risk capabilities: classification

### `core.knowledge_mapper.indexer`
- Package: `core/knowledge_mapper`
- Path: `core/knowledge_mapper/indexer.py`
- Duplicate-risk capabilities: classification, reading
- Functions: build_subject_index

### `core.knowledge_mapper.mapper`
- Package: `core/knowledge_mapper`
- Path: `core/knowledge_mapper/mapper.py`
- Duplicate-risk capabilities: classification
- Functions: map_path

### `core.knowledge_mapper.models`
- Package: `core/knowledge_mapper`
- Path: `core/knowledge_mapper/models.py`
- Duplicate-risk capabilities: classification

### `core.knowledge_mapper.report`
- Package: `core/knowledge_mapper`
- Path: `core/knowledge_mapper/report.py`
- Duplicate-risk capabilities: classification
- Functions: print_summary

### `core.knowledge_mapper.rules`
- Package: `core/knowledge_mapper`
- Path: `core/knowledge_mapper/rules.py`
- Duplicate-risk capabilities: classification
- Functions: load_rules

### `core.semantic_digest.__init__`
- Package: `core/semantic_digest`
- Path: `core/semantic_digest/__init__.py`
- Duplicate-risk capabilities: classification

### `core.semantic_digest.analyzer`
- Package: `core/semantic_digest`
- Path: `core/semantic_digest/analyzer.py`
- Duplicate-risk capabilities: classification, extraction, graph, normalization, reading
- Functions: load_rules, normalize, analyze_semantics

### `core.semantic_digest.cli`
- Package: `core/semantic_digest`
- Path: `core/semantic_digest/cli.py`
- Duplicate-risk capabilities: catalog, classification, inspection
- Functions: cmd_inspect, cmd_digest, main

### `core.semantic_digest.inspector`
- Package: `core/semantic_digest`
- Path: `core/semantic_digest/inspector.py`
- Duplicate-risk capabilities: catalog, classification, inspection, reading
- Classes: DocumentInspection
- Functions: inspect_document

### `core.semantic_digest.pipeline`
- Package: `core/semantic_digest`
- Path: `core/semantic_digest/pipeline.py`
- Duplicate-risk capabilities: catalog, classification, extraction, inspection, reading
- Functions: process_document

### `core.semantic_digest.readers`
- Package: `core/semantic_digest`
- Path: `core/semantic_digest/readers.py`
- Duplicate-risk capabilities: catalog, chunking, classification, extraction, inspection, reading
- Functions: read_text_file, read_pdf, read_document

### `core.semantic_digest.structural`
- Package: `core/semantic_digest`
- Path: `core/semantic_digest/structural.py`
- Duplicate-risk capabilities: classification, extraction, reading
- Functions: clean_line, extract_headings, extract_terms, extract_structure

### `dev.librarian.acquire_pipeline`
- Package: `dev/librarian`
- Path: `dev/librarian/acquire_pipeline.py`
- Duplicate-risk capabilities: acquisition, catalog, extraction, normalization
- Functions: process_zip, main

### `dev.librarian.acquisition.archive`
- Package: `dev/librarian`
- Path: `dev/librarian/acquisition/archive.py`
- Duplicate-risk capabilities: normalization
- Functions: archive

### `dev.librarian.acquisition.filter`
- Package: `dev/librarian`
- Path: `dev/librarian/acquisition/filter.py`
- Duplicate-risk capabilities: discovery, reading
- Functions: should_keep

### `dev.librarian.acquisition.manifest`
- Package: `dev/librarian`
- Path: `dev/librarian/acquisition/manifest.py`
- Duplicate-risk capabilities: chunking, discovery, normalization
- Functions: sha256_file, append_manifest

### `dev.librarian.acquisition.metadata`
- Package: `dev/librarian`
- Path: `dev/librarian/acquisition/metadata.py`
- Duplicate-risk capabilities: extraction, reading
- Functions: load_json, extract_course_metadata, write_metadata

### `dev.librarian.acquisition.normalize`
- Package: `dev/librarian`
- Path: `dev/librarian/acquisition/normalize.py`
- Duplicate-risk capabilities: catalog, classification, discovery, extraction, normalization, reading
- Functions: extract_zip, classify_kind, copy_useful_assets

### `dev.librarian.acquisition.pipeline`
- Package: `dev/librarian`
- Path: `dev/librarian/acquisition/pipeline.py`
- Duplicate-risk capabilities: acquisition, extraction, normalization
- Functions: process

### `dev.librarian.cko.database`
- Package: `dev/librarian`
- Path: `dev/librarian/cko/database.py`
- Duplicate-risk capabilities: discovery, inspection, reading, storage
- Functions: connect, migrate

### `dev.librarian.cko.mit_cko_builder`
- Package: `dev/librarian`
- Path: `dev/librarian/cko/mit_cko_builder.py`
- Duplicate-risk capabilities: acquisition, chunking, discovery, extraction, inspection, normalization, reading, search, storage
- Functions: utc_now, sha256_file, safe_name, load_json, guess_type, find_course_root, extract_title, collect_static_pdfs, find_pdf_for_resource, add_cko, add_representation, materialize_representation, build_course, main

### `dev.librarian.discover`
- Package: `dev/librarian`
- Path: `dev/librarian/discover.py`
- Duplicate-risk capabilities: discovery, search
- Functions: main

### `dev.librarian.discovery.__init__`
- Package: `dev/librarian`
- Path: `dev/librarian/discovery/__init__.py`
- Duplicate-risk capabilities: discovery

### `dev.librarian.discovery.engine`
- Package: `dev/librarian`
- Path: `dev/librarian/discovery/engine.py`
- Duplicate-risk capabilities: acquisition, discovery, graph, normalization, reading, search
- Functions: normalize_topic, human_topic, slugify, load_sources, source_matches_topic, score_candidate, discover, write_discovery_plan

### `dev.librarian.discovery.models`
- Package: `dev/librarian`
- Path: `dev/librarian/discovery/models.py`
- Duplicate-risk capabilities: discovery, search
- Classes: TrustedSource, DiscoveryCandidate
- Functions: utc_now, to_dict

### `dev.librarian.inventory.inventory`
- Package: `dev/librarian`
- Path: `dev/librarian/inventory/inventory.py`
- Duplicate-risk capabilities: catalog, reading

### `dev.librarian.librarian`
- Package: `dev/librarian`
- Path: `dev/librarian/librarian.py`
- Duplicate-risk capabilities: catalog
- Functions: register

### `dev.librarian.mit_miner`
- Package: `dev/librarian`
- Path: `dev/librarian/mit_miner.py`
- Duplicate-risk capabilities: acquisition, chunking, normalization, reading, search
- Functions: sha256, search, mine_course, download, main

### `dev.librarian.mit_targeted_miner`
- Package: `dev/librarian`
- Path: `dev/librarian/mit_targeted_miner.py`
- Duplicate-risk capabilities: acquisition, chunking, discovery, extraction, inspection, normalization, reading
- Classes: Links
- Functions: fetch, text_from_html, sha256_file, safe_name, write_manifest, download, mine_ocw_course_zip, mine_mit_press_books, main, handle_starttag

### `dev.librarian.pdf_hunter`
- Package: `dev/librarian`
- Path: `dev/librarian/pdf_hunter.py`
- Duplicate-risk capabilities: acquisition, chunking, normalization, reading, search, storage
- Classes: LinkParser
- Functions: sha256_file, fetch, safe_filename, same_domain, robots_allowed, crawl, main, handle_starttag

### `dev.librarian.run_pipeline`
- Package: `dev/librarian`
- Path: `dev/librarian/run_pipeline.py`
- Duplicate-risk capabilities: acquisition, discovery, extraction

### `knowledge_engine.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/__init__.py`
- Duplicate-risk capabilities: search

### `knowledge_engine.catalog`
- Package: `knowledge_engine`
- Path: `knowledge_engine/catalog.py`
- Duplicate-risk capabilities: catalog, discovery, extraction, inspection, reading, storage
- Classes: KnowledgeCatalog
- Functions: connect, initialize, upsert_document, upsert_inspection, summary, duplicate_groups, replace_structure, structure_summary

### `knowledge_engine.catalog.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/catalog/__init__.py`
- Duplicate-risk capabilities: catalog

### `knowledge_engine.chunking.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/chunking/__init__.py`
- Duplicate-risk capabilities: chunking

### `knowledge_engine.chunking.chunker`
- Package: `knowledge_engine`
- Path: `knowledge_engine/chunking/chunker.py`
- Duplicate-risk capabilities: chunking

### `knowledge_engine.cli`
- Package: `knowledge_engine`
- Path: `knowledge_engine/cli.py`
- Duplicate-risk capabilities: catalog, discovery, extraction, inspection, storage
- Functions: section, main

### `knowledge_engine.collections.store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/collections/store.py`
- Duplicate-risk capabilities: storage

### `knowledge_engine.concepts.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/concepts/__init__.py`
- Duplicate-risk capabilities: classification

### `knowledge_engine.discovery.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/discovery/__init__.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.discovery.scanner`
- Package: `knowledge_engine`
- Path: `knowledge_engine/discovery/scanner.py`
- Duplicate-risk capabilities: discovery
- Functions: discover_files

### `knowledge_engine.document`
- Package: `knowledge_engine`
- Path: `knowledge_engine/document.py`
- Duplicate-risk capabilities: catalog
- Classes: DocumentRecord
- Functions: relative_path

### `knowledge_engine.embeddings.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/embeddings/__init__.py`
- Duplicate-risk capabilities: embedding

### `knowledge_engine.embeddings.engine`
- Package: `knowledge_engine`
- Path: `knowledge_engine/embeddings/engine.py`
- Duplicate-risk capabilities: embedding

### `knowledge_engine.extraction.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/extraction/__init__.py`
- Duplicate-risk capabilities: extraction

### `knowledge_engine.extraction.extractors.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/extraction/extractors/__init__.py`
- Duplicate-risk capabilities: extraction

### `knowledge_engine.extraction.extractors.base`
- Package: `knowledge_engine`
- Path: `knowledge_engine/extraction/extractors/base.py`
- Duplicate-risk capabilities: extraction
- Classes: BaseExtractor
- Functions: supports, extract

### `knowledge_engine.extraction.extractors.pdf`
- Package: `knowledge_engine`
- Path: `knowledge_engine/extraction/extractors/pdf.py`
- Duplicate-risk capabilities: catalog, extraction, reading
- Classes: PDFExtractor
- Functions: supports, extract

### `knowledge_engine.index.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/index/__init__.py`
- Duplicate-risk capabilities: search, storage

### `knowledge_engine.index.builder`
- Package: `knowledge_engine`
- Path: `knowledge_engine/index/builder.py`
- Duplicate-risk capabilities: catalog, classification, extraction, inspection, storage
- Classes: KnowledgeIndexBuilder
- Functions: build

### `knowledge_engine.index.models`
- Package: `knowledge_engine`
- Path: `knowledge_engine/index/models.py`
- Duplicate-risk capabilities: catalog, classification, extraction
- Classes: IndexRecord

### `knowledge_engine.index.search`
- Package: `knowledge_engine`
- Path: `knowledge_engine/index/search.py`
- Duplicate-risk capabilities: catalog, classification, extraction, search
- Classes: KnowledgeIndexSearch
- Functions: search

### `knowledge_engine.index.store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/index/store.py`
- Duplicate-risk capabilities: catalog, classification, extraction, storage
- Classes: KnowledgeIndexStore
- Functions: upsert, summary

### `knowledge_engine.inspection.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspection/__init__.py`
- Duplicate-risk capabilities: inspection

### `knowledge_engine.inspectors.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/__init__.py`
- Duplicate-risk capabilities: inspection

### `knowledge_engine.inspectors.base`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/base.py`
- Duplicate-risk capabilities: catalog, extraction, inspection, reading
- Classes: BaseInspector
- Functions: inspect, extract_text

### `knowledge_engine.inspectors.docx`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/docx.py`
- Duplicate-risk capabilities: catalog, graph, inspection, reading
- Classes: DocxInspector
- Functions: inspect

### `knowledge_engine.inspectors.epub`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/epub.py`
- Duplicate-risk capabilities: extraction, inspection, reading
- Classes: EpubInspector
- Functions: inspect

### `knowledge_engine.inspectors.html`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/html.py`
- Duplicate-risk capabilities: inspection, reading
- Classes: HtmlInspector
- Functions: inspect

### `knowledge_engine.inspectors.image`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/image.py`
- Duplicate-risk capabilities: inspection
- Classes: ImageInspector
- Functions: inspect

### `knowledge_engine.inspectors.markdown`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/markdown.py`
- Duplicate-risk capabilities: inspection, reading
- Classes: MarkdownInspector

### `knowledge_engine.inspectors.pdf`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/pdf.py`
- Duplicate-risk capabilities: extraction, inspection, reading, search
- Classes: PDFInspector
- Functions: inspect

### `knowledge_engine.inspectors.registry`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/registry.py`
- Duplicate-risk capabilities: catalog, inspection, reading
- Classes: InspectorRegistry
- Functions: register, get

### `knowledge_engine.inspectors.text`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/text.py`
- Duplicate-risk capabilities: inspection, reading
- Classes: TextInspector
- Functions: inspect

### `knowledge_engine.inspectors.zim`
- Package: `knowledge_engine`
- Path: `knowledge_engine/inspectors/zim.py`
- Duplicate-risk capabilities: inspection, reading
- Classes: ZimInspector
- Functions: inspect

### `knowledge_engine.library.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/library/__init__.py`
- Duplicate-risk capabilities: catalog, storage

### `knowledge_engine.library.builder`
- Package: `knowledge_engine`
- Path: `knowledge_engine/library/builder.py`
- Duplicate-risk capabilities: catalog, classification, discovery, extraction, inspection, storage
- Classes: LibraryCatalogBuilder
- Functions: build

### `knowledge_engine.library.models`
- Package: `knowledge_engine`
- Path: `knowledge_engine/library/models.py`
- Duplicate-risk capabilities: catalog, classification, discovery
- Classes: LibraryRecord

### `knowledge_engine.library.store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/library/store.py`
- Duplicate-risk capabilities: catalog, classification, discovery, storage
- Classes: LibraryCatalogStore
- Functions: upsert, summary

### `knowledge_engine.metadata.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/metadata/__init__.py`
- Duplicate-risk capabilities: extraction

### `knowledge_engine.metadata.fingerprints`
- Package: `knowledge_engine`
- Path: `knowledge_engine/metadata/fingerprints.py`
- Duplicate-risk capabilities: chunking, extraction
- Functions: sha256_file

### `knowledge_engine.pages.models`
- Package: `knowledge_engine`
- Path: `knowledge_engine/pages/models.py`
- Duplicate-risk capabilities: catalog, reading
- Classes: Page

### `knowledge_engine.pages.store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/pages/store.py`
- Duplicate-risk capabilities: catalog, reading, storage
- Classes: PageStore
- Functions: replace_pages

### `knowledge_engine.pipeline`
- Package: `knowledge_engine`
- Path: `knowledge_engine/pipeline.py`
- Duplicate-risk capabilities: catalog, extraction, inspection
- Functions: run_inventory

### `knowledge_engine.processing.catalog_stage`
- Package: `knowledge_engine`
- Path: `knowledge_engine/processing/catalog_stage.py`
- Duplicate-risk capabilities: catalog, discovery, extraction, storage
- Classes: CatalogStage
- Functions: category_from_path, build_record, run

### `knowledge_engine.processing.chunk_stage`
- Package: `knowledge_engine`
- Path: `knowledge_engine/processing/chunk_stage.py`
- Duplicate-risk capabilities: chunking

### `knowledge_engine.processing.concept_stage`
- Package: `knowledge_engine`
- Path: `knowledge_engine/processing/concept_stage.py`
- Duplicate-risk capabilities: classification

### `knowledge_engine.processing.discover`
- Package: `knowledge_engine`
- Path: `knowledge_engine/processing/discover.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.processing.extract_stage`
- Package: `knowledge_engine`
- Path: `knowledge_engine/processing/extract_stage.py`
- Duplicate-risk capabilities: extraction

### `knowledge_engine.processing.extract_text_stage`
- Package: `knowledge_engine`
- Path: `knowledge_engine/processing/extract_text_stage.py`
- Duplicate-risk capabilities: catalog, extraction, reading, storage
- Classes: ExtractTextStage
- Functions: run

### `knowledge_engine.processing.inspect_stage`
- Package: `knowledge_engine`
- Path: `knowledge_engine/processing/inspect_stage.py`
- Duplicate-risk capabilities: catalog, extraction, inspection, storage
- Classes: InspectStage
- Functions: run

### `knowledge_engine.processing.processor`
- Package: `knowledge_engine`
- Path: `knowledge_engine/processing/processor.py`
- Duplicate-risk capabilities: catalog, extraction, inspection, storage
- Classes: ProcessingEngine
- Functions: run_foundation

### `knowledge_engine.processing.retrieve_stage`
- Package: `knowledge_engine`
- Path: `knowledge_engine/processing/retrieve_stage.py`
- Duplicate-risk capabilities: search

### `knowledge_engine.processing.structure_stage`
- Package: `knowledge_engine`
- Path: `knowledge_engine/processing/structure_stage.py`
- Duplicate-risk capabilities: catalog, extraction, storage
- Classes: StructureStage
- Functions: run

### `knowledge_engine.providers.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/providers/__init__.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.providers.base`
- Package: `knowledge_engine`
- Path: `knowledge_engine/providers/base.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.providers.faa`
- Package: `knowledge_engine`
- Path: `knowledge_engine/providers/faa.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.providers.local`
- Package: `knowledge_engine`
- Path: `knowledge_engine/providers/local.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.providers.nasa`
- Package: `knowledge_engine`
- Path: `knowledge_engine/providers/nasa.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.providers.noaa`
- Package: `knowledge_engine`
- Path: `knowledge_engine/providers/noaa.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.providers.provider`
- Package: `knowledge_engine`
- Path: `knowledge_engine/providers/provider.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.providers.registry`
- Package: `knowledge_engine`
- Path: `knowledge_engine/providers/registry.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.providers.us_army`
- Package: `knowledge_engine`
- Path: `knowledge_engine/providers/us_army.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.providers.who`
- Package: `knowledge_engine`
- Path: `knowledge_engine/providers/who.py`
- Duplicate-risk capabilities: discovery

### `knowledge_engine.queue.builder`
- Package: `knowledge_engine`
- Path: `knowledge_engine/queue/builder.py`
- Duplicate-risk capabilities: catalog
- Classes: ProcessingQueueBuilder
- Functions: build

### `knowledge_engine.queue.models`
- Package: `knowledge_engine`
- Path: `knowledge_engine/queue/models.py`
- Duplicate-risk capabilities: catalog
- Classes: QueueItem

### `knowledge_engine.queue.priorities`
- Package: `knowledge_engine`
- Path: `knowledge_engine/queue/priorities.py`
- Duplicate-risk capabilities: graph, normalization

### `knowledge_engine.readers`
- Package: `knowledge_engine`
- Path: `knowledge_engine/readers.py`
- Duplicate-risk capabilities: reading
- Functions: read_pdf_pages

### `knowledge_engine.reports.duplicates`
- Package: `knowledge_engine`
- Path: `knowledge_engine/reports/duplicates.py`
- Duplicate-risk capabilities: reading
- Functions: write_duplicates_csv, write_duplicates_markdown

### `knowledge_engine.search.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/search/__init__.py`
- Duplicate-risk capabilities: search

### `knowledge_engine.search.local_search`
- Package: `knowledge_engine`
- Path: `knowledge_engine/search/local_search.py`
- Duplicate-risk capabilities: search

### `knowledge_engine.search.retrieval`
- Package: `knowledge_engine`
- Path: `knowledge_engine/search/retrieval.py`
- Duplicate-risk capabilities: search

### `knowledge_engine.storage.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/storage/__init__.py`
- Duplicate-risk capabilities: storage

### `knowledge_engine.storage.catalog_store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/storage/catalog_store.py`
- Duplicate-risk capabilities: catalog, storage
- Classes: CatalogStore
- Functions: upsert_document, summary

### `knowledge_engine.storage.chunk_store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/storage/chunk_store.py`
- Duplicate-risk capabilities: chunking, storage

### `knowledge_engine.storage.concept_store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/storage/concept_store.py`
- Duplicate-risk capabilities: classification, storage

### `knowledge_engine.storage.database`
- Package: `knowledge_engine`
- Path: `knowledge_engine/storage/database.py`
- Duplicate-risk capabilities: catalog, chunking, classification, discovery, extraction, inspection, reading, storage
- Classes: KnowledgeDatabase
- Functions: connect, initialize

### `knowledge_engine.storage.inspection_store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/storage/inspection_store.py`
- Duplicate-risk capabilities: catalog, extraction, inspection, storage
- Classes: InspectionStore
- Functions: upsert

### `knowledge_engine.storage.page_store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/storage/page_store.py`
- Duplicate-risk capabilities: catalog, reading, search, storage
- Classes: PageStore
- Functions: replace_pages, search

### `knowledge_engine.storage.structure_store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/storage/structure_store.py`
- Duplicate-risk capabilities: catalog, discovery, extraction, storage
- Classes: StructureStore
- Functions: replace, summary

### `knowledge_engine.storage.text_store`
- Package: `knowledge_engine`
- Path: `knowledge_engine/storage/text_store.py`
- Duplicate-risk capabilities: catalog, extraction, reading, storage
- Classes: TextStore
- Functions: upsert

### `knowledge_engine.structure.__init__`
- Package: `knowledge_engine`
- Path: `knowledge_engine/structure/__init__.py`
- Duplicate-risk capabilities: extraction

### `knowledge_engine.structure.base`
- Package: `knowledge_engine`
- Path: `knowledge_engine/structure/base.py`
- Duplicate-risk capabilities: catalog, discovery, extraction
- Classes: StructureNode

### `knowledge_engine.structure.pdf`
- Package: `knowledge_engine`
- Path: `knowledge_engine/structure/pdf.py`
- Duplicate-risk capabilities: catalog, discovery, extraction, reading
- Classes: PDFStructureExtractor
- Functions: extract

### `knowledge_engine.structure.registry`
- Package: `knowledge_engine`
- Path: `knowledge_engine/structure/registry.py`
- Duplicate-risk capabilities: catalog, extraction, reading
- Classes: StructureRegistry
- Functions: register, get
