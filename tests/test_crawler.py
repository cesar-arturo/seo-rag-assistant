from seo_rag.ingestion.crawler import crawl, extract_links, normalize_url

PREFIX = "https://developers.google.com/search/docs"


def test_normalize_url_drops_query_fragment_and_trailing_slash():
    assert (
        normalize_url("https://Developers.Google.com/search/docs/basics/?hl=es#intro")
        == "https://developers.google.com/search/docs/basics"
    )


def test_extract_links_keeps_only_in_scope_pages():
    html = """
        <a href="/search/docs/appearance">relative</a>
        <a href="https://developers.google.com/search/docs/crawling-indexing#robots">absolute</a>
        <a href="appearance/title-link">relative to page</a>
        <a href="/search/blog/2025/01/post">other section</a>
        <a href="/search/docs-other">look-alike prefix</a>
        <a href="/search/docs/guide.pdf">pdf</a>
        <a href="https://example.com/search/docs">other host</a>
        <a>no href</a>
    """
    assert extract_links(html, PREFIX + "/", PREFIX) == {
        PREFIX + "/appearance",
        PREFIX + "/crawling-indexing",
        PREFIX + "/appearance/title-link",
    }


class FakeResponse:
    def __init__(self, url, html, status=200):
        self.url, self.text, self.status_code = url, html, status
        self.ok = status < 400
        self.headers = {"content-type": "text/html; charset=utf-8"}


class FakeSession:
    def __init__(self, pages):
        self.pages, self.headers, self.requested = pages, {}, []

    def get(self, url, timeout):
        self.requested.append(url)
        if url not in self.pages:
            return FakeResponse(url, "", status=404)
        return FakeResponse(url, self.pages[url])


def test_crawl_follows_links_once_and_respects_max_pages():
    session = FakeSession(
        {
            PREFIX: '<a href="/search/docs/a">a</a><a href="/search/docs/b">b</a>',
            PREFIX + "/a": '<a href="/search/docs">home</a><a href="/search/docs/b">b</a>',
            PREFIX + "/b": '<a href="/search/docs/missing">missing</a>',
        }
    )

    pages = list(crawl(PREFIX, PREFIX, delay_seconds=0, session=session))

    assert [p.url for p in pages] == [PREFIX, PREFIX + "/a", PREFIX + "/b", PREFIX + "/missing"]
    assert pages[-1].status == 404 and pages[-1].html is None
    assert session.requested == [p.url for p in pages]

    limited = list(crawl(PREFIX, PREFIX, max_pages=2, delay_seconds=0, session=session))
    assert len(limited) == 2
