"""Tests for Phase X-C1 Cognitive Representation."""

from __future__ import annotations

import unittest

from core.representation import ArtifactKind, SegmentKind, segment_text


class CognitiveRepresentationTests(unittest.TestCase):
    def test_empty_text(self) -> None:
        result = segment_text(artifact_id="empty", text="")
        self.assertEqual(result.segment_count, 0)

    def test_heading_and_sentences(self) -> None:
        text = "Operational Assessment\n\nPrimary online. Backup available."
        result = segment_text(artifact_id="a1", text=text)
        self.assertEqual(
            tuple(s.kind for s in result.segments),
            (SegmentKind.HEADING, SegmentKind.SENTENCE, SegmentKind.SENTENCE),
        )

    def test_bullets(self) -> None:
        text = "- Verify source.\n- Preserve provenance."
        result = segment_text(artifact_id="b1", text=text)
        self.assertTrue(all(s.kind is SegmentKind.BULLET for s in result.segments))

    def test_decimal(self) -> None:
        result = segment_text(
            artifact_id="d1",
            text="Efficiency declined by 40.5 percent. Recovery followed.",
        )
        self.assertEqual(result.segment_count, 2)

    def test_code(self) -> None:
        result = segment_text(
            artifact_id="c1",
            text="```python\nprint('hello')\n```",
            artifact_kind=ArtifactKind.SOURCE_CODE,
        )
        self.assertEqual(result.segments[0].kind, SegmentKind.CODE)

    def test_table_rows(self) -> None:
        result = segment_text(
            artifact_id="t1",
            text="| Key | Value |\n| --- | --- |\n| A | 1 |",
        )
        self.assertTrue(all(s.kind is SegmentKind.TABLE_ROW for s in result.segments))

    def test_key_value(self) -> None:
        result = segment_text(artifact_id="k1", text="Status: online\nOwner: JARVIS")
        self.assertTrue(all(s.kind is SegmentKind.KEY_VALUE for s in result.segments))

    def test_offsets(self) -> None:
        text = "Status\n\nSystem stable. No fault detected."
        result = segment_text(artifact_id="o1", text=text)
        for segment in result.segments:
            self.assertEqual(text[segment.span.start:segment.span.end].strip(), segment.text)

    def test_determinism(self) -> None:
        text = "Review\n\nPrimary responded. Secondary failed."
        first = segment_text(artifact_id="same", text=text)
        second = segment_text(artifact_id="same", text=text)
        self.assertEqual(first, second)

    def test_source_identity_changes_ids(self) -> None:
        text = "System operational."
        a = segment_text(artifact_id="a", text=text)
        b = segment_text(artifact_id="b", text=text)
        self.assertNotEqual(a.segments[0].segment_id, b.segments[0].segment_id)


if __name__ == "__main__":
    unittest.main()
