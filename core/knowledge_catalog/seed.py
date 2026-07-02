from __future__ import annotations

from core.knowledge_catalog.models import Source, Topic
from core.knowledge_catalog.repository import CatalogRepository


TOPIC_PATHS = [
    "aviation",
    "aviation/aircraft",
    "aviation/maintenance",
    "aviation/navigation",
    "aviation/regulations",
    "aviation/rotorcraft",
    "aviation/systems",

    "computing",
    "computing/ai",
    "computing/cybersecurity",
    "computing/databases",
    "computing/linux",
    "computing/networking",
    "computing/operating_systems",
    "computing/programming",
    "computing/reverse_engineering",
    "computing/software_engineering",
    "computing/virtualization",
    "computing/distributed_systems",
    "computing/compilers",
    "computing/cryptography",

    "engineering",
    "engineering/civil",
    "engineering/electrical",
    "engineering/electronics",
    "engineering/manufacturing",
    "engineering/materials",
    "engineering/mechanical",
    "engineering/control_systems",
    "engineering/hydraulics",
    "engineering/thermodynamics",
    "engineering/robotics",
    "engineering/embedded_systems",

    "mathematics",
    "mathematics/algebra",
    "mathematics/calculus",
    "mathematics/discrete_math",
    "mathematics/linear_algebra",
    "mathematics/statistics",
    "mathematics/probability",
    "mathematics/optimization",
    "mathematics/numerical_methods",

    "medical",
    "medical/anatomy",
    "medical/community_health",
    "medical/dentistry",
    "medical/emergency",
    "medical/field_medicine",
    "medical/first_aid",
    "medical/medications",
    "medical/mental_health",
    "medical/obstetrics",
    "medical/pediatrics",
    "medical/public_health",
    "medical/reference",
    "medical/surgery",
    "medical/radiology",
    "medical/pharmacology",
    "medical/tropical_medicine",
    "medical/wilderness_medicine",
    "medical/prolonged_field_care",

    "science",
    "science/biology",
    "science/chemistry",
    "science/earth_science",
    "science/physics",
    "science/astronomy",

    "emergency",
    "emergency/civil_defense",
    "emergency/disaster_response",
    "emergency/communications",
    "emergency/survival",
    "emergency/water",
    "emergency/wilderness",

    "military",
    "military/doctrine",
    "military/field_manuals",
    "military/navigation",
    "military/tactics",
    "military/training",

    "reference",
    "reference/handbooks",
    "reference/manuals",
    "reference/standards",

    "zim",
    "zim/libretexts",
    "zim/stackexchange",
    "zim/wikipedia",
    "zim/wikibooks",
    "zim/ifixit",
]


SOURCES = [
    Source("MIT OpenCourseWare", 0, "university", "https://ocw.mit.edu"),
    Source("OpenStax", 0, "open_textbook", "https://openstax.org"),
    Source("LibreTexts", 0, "open_textbook", "https://libretexts.org"),
    Source("WHO", 0, "public_health", "https://www.who.int"),
    Source("CDC", 0, "public_health", "https://www.cdc.gov"),
    Source("NIH", 0, "medical", "https://www.nih.gov"),
    Source("PubMed Central", 0, "medical_journal", "https://pmc.ncbi.nlm.nih.gov"),
    Source("NIST", 0, "standards", "https://www.nist.gov"),
    Source("NASA", 0, "government", "https://www.nasa.gov"),
    Source("FAA", 0, "aviation", "https://www.faa.gov"),
    Source("FEMA", 0, "emergency_management", "https://www.fema.gov"),
    Source("US Army", 1, "military", None),
    Source("USMC", 1, "military", None),
    Source("Hesperian", 1, "medical", "https://hesperian.org"),
    Source("StackExchange", 1, "community_qa", "https://stackexchange.com"),
    Source("iFixit", 1, "repair", "https://www.ifixit.com"),
    Source("Wikibooks", 1, "open_reference", "https://www.wikibooks.org"),
]


def seed_catalog(repo: CatalogRepository) -> None:
    for source in SOURCES:
        repo.upsert_source(source)

    for path in TOPIC_PATHS:
        parts = path.split("/")
        name = parts[-1].replace("_", " ").title()
        parent = "/".join(parts[:-1]) if len(parts) > 1 else None
        desired_depth = "high" if path.startswith(("medical", "computing", "engineering")) else "medium"
        repo.upsert_topic(Topic(path=path, name=name, parent_path=parent, desired_depth=desired_depth))
