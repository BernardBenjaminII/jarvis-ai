# ADR-0012: Knowledge Coverage Graph

## Status

Accepted

---

# Context

The purpose of JARVIS is not to accumulate documents.

The purpose of JARVIS is to understand, organize, expand, and teach knowledge.

Traditional Retrieval-Augmented Generation (RAG) systems measure documents.

JARVIS measures knowledge.

Therefore JARVIS requires an explicit model describing:

- what knowledge exists
- how knowledge is related
- how complete JARVIS is
- what knowledge is missing
- where additional knowledge should be acquired

This model is called the Knowledge Coverage Graph.

---

# Decision

JARVIS shall represent knowledge as a weighted directed graph.

The graph represents concepts rather than files.

Files are evidence.

Knowledge consists of interconnected concepts.

Every subsystem contributes to this graph.

---

# Core Principle

Knowledge is represented by Concepts.

Documents support Concepts.

Sources provide Authority.

Relationships define Understanding.

Coverage measures Completeness.

Curiosity drives Growth.

---

# Graph Model

Human Knowledge

↓

Domains

↓

Disciplines

↓

Subjects

↓

Topics

↓

Concepts

↓

Knowledge Objects

↓

Evidence

Example

Engineering

↓

Mechanical Engineering

↓

Thermodynamics

↓

Heat Transfer

↓

Conduction

↓

Fourier's Law

↓

CKOs

↓

MIT

OpenStax

NASA

NIST

---

# Hierarchy

The graph shall contain multiple levels.

Level 0

Human Knowledge

Level 1

Major Domains

Examples

Mathematics

Medicine

Engineering

Computer Science

Physics

Religion

History

Agriculture

Emergency Preparedness

Level 2

Disciplines

Examples

Mechanical Engineering

Electrical Engineering

Trauma Surgery

Machine Learning

Topology

Microbiology

Level 3

Topics

Examples

Linear Algebra

Fluid Mechanics

Radiology

Networking

Orthopedics

Level 4

Concepts

Examples

Eigenvalues

Laminar Flow

TCP Three-Way Handshake

Damage Control Resuscitation

Level 5

Knowledge Objects

Canonical Knowledge Objects

Level 6

Evidence

PDFs

Books

Journals

HTML

Markdown

Wikipedia

Videos

ZIM

XML

JSON

---

# Relationships

The graph supports relationships.

Examples

depends_on

prerequisite_of

part_of

derived_from

similar_to

contradicts

extends

references

authoritative_source

teaches

uses

---

# Authority

Every evidence source has an authority score.

Example

WHO

100

MIT

100

NASA

98

NIST

98

FAA

98

CDC

98

OpenStax

95

LibreTexts

92

Wikipedia

80

Personal Blog

20

Authority influences confidence.

Authority never replaces evidence.

---

# Confidence

Every Concept has confidence.

Confidence is computed from

Source authority

Number of independent sources

Agreement

Freshness

Quality of extraction

Example

Fourier's Law

Confidence

99.8%

because

MIT

OpenStax

NASA

NIST

agree.

---

# Coverage

Coverage is the central metric.

Coverage is not based on document count.

Coverage estimates conceptual completeness.

Example

Linear Algebra

Coverage

91%

because

MIT course

✓

OpenStax

✓

Exercises

✓

Solutions

✓

Reference texts

✓

Research papers

partial

---

# Coverage Dimensions

Coverage includes

Breadth

How many concepts exist.

Depth

How thoroughly concepts are documented.

Authority

How trustworthy the evidence is.

Freshness

Whether information is current.

Diversity

How many independent sources exist.

Completeness

Whether prerequisite concepts exist.

---

# Prerequisite Graph

Knowledge has dependencies.

Example

Machine Learning

depends on

Probability

Linear Algebra

Optimization

Statistics

Programming

JARVIS should identify weak prerequisite areas before expanding advanced topics.

---

# Knowledge Density

Different concepts require different amounts of evidence.

Example

CPR

May require

5

excellent manuals.

Machine Learning

May require

300

books

courses

papers

projects

Coverage targets shall be configurable.

---

# Knowledge Campaigns

Campaigns are groups of acquisition goals.

Examples

Medical School

Mechanical Engineering

MIT Undergraduate Mathematics

Emergency Preparedness

Islamic Studies

Aviation Maintenance

Campaigns measure progress using graph coverage.

---

# Gap Analysis

Coverage gaps are automatically identified.

Example

Medicine

Coverage

72%

Weak Areas

Burn Surgery

Neurosurgery

Pediatric Trauma

Recommendations

WHO

PubMed Central

US Army Institute of Surgical Research

---

# Curiosity

Curiosity is a system capability.

JARVIS continuously evaluates

What do I know?

What do I not know?

What should I learn next?

What authoritative sources should I consult?

Curiosity generates acquisition missions.

---

# Teaching

The graph supports teaching.

Because prerequisites are encoded,

JARVIS can generate learning paths.

Example

Become an Aerospace Engineer

↓

Calculus

↓

Linear Algebra

↓

Physics

↓

Statics

↓

Dynamics

↓

Thermodynamics

↓

Fluid Mechanics

↓

Aerodynamics

↓

Flight Mechanics

↓

Propulsion

---

# Success Criteria

The Knowledge Coverage Graph is successful when JARVIS can answer

What do I know?

How well do I know it?

What is missing?

What should I acquire next?

Which source is most authoritative?

Which prerequisite concepts are incomplete?

Can I teach this subject?

---

# Consequences

Future ADRs will extend this graph.

Examples

ADR-0013

Gap Analysis Engine

ADR-0014

Knowledge Campaigns

ADR-0015

Autonomous Research Planner

ADR-0016

Teaching Engine

ADR-0017

Knowledge Evolution

All future acquisition, ingestion, retrieval, and reasoning components shall integrate with the Knowledge Coverage Graph.
