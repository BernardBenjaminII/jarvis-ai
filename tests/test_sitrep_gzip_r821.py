import gzip
import io
from datetime import datetime, timezone
from email.utils import format_datetime

import pytest

from core.sitrep.security_news import (
    MAX_BYTES,
    SecurityFeed,
    decode_feed_body,
)


def rss_body():
    published = format_datetime(datetime.now(timezone.utc))
    return f"""<?xml version="1.0" encoding="UTF-8"?>
    <rss version="2.0">
      <channel>
        <title>Security Feed</title>
        <item>
          <title>Military security alert</title>
          <link>https://news.un.org/example-report</link>
          <description>Military conflict and security update</description>
          <pubDate>{published}</pubDate>
        </item>
      </channel>
    </rss>""".encode("utf-8")


class FakeResponse(io.BytesIO):
    def __init__(self, body, headers=None):
        super().__init__(body)
        self.headers = headers or {}


@pytest.mark.parametrize("compressed", [False, True])
def test_security_feed_collection(compressed):
    body = rss_body()
    if compressed:
        body = gzip.compress(body)

    feed = SecurityFeed(
        "un_peace_security",
        "UN News",
        "https://news.un.org/feed.xml",
        "physical",
        opener=lambda request, timeout: FakeResponse(body),
    )

    result = feed.collect()

    assert result["provider_id"] == "un_peace_security"
    assert len(result["security_events"]) == 1


def test_gzip_content_encoding_header():
    body = gzip.compress(rss_body())

    feed = SecurityFeed(
        "un_peace_security",
        "UN News",
        "https://news.un.org/feed.xml",
        "physical",
        opener=lambda request, timeout: FakeResponse(
            body, {"Content-Encoding": "gzip"}
        ),
    )

    assert len(feed.collect()["security_events"]) == 1


def test_invalid_gzip_rejected():
    with pytest.raises(ValueError, match="Invalid GZIP"):
        decode_feed_body(b"not valid gzip", "gzip")


def test_decompression_bomb_rejected():
    oversized = gzip.compress(b"A" * (MAX_BYTES + 1))

    with pytest.raises(ValueError, match="exceeds size limit"):
        decode_feed_body(oversized)


def test_xml_security_restriction_preserved():
    body = b'<!DOCTYPE rss><rss version="2.0"></rss>'

    feed = SecurityFeed(
        "un_peace_security",
        "UN News",
        "https://news.un.org/feed.xml",
        "physical",
    )

    with pytest.raises(ValueError, match="XML declarations not allowed"):
        feed.parse(body)
