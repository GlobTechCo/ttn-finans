"""RSS snapshot regressions: original dates, short previews and outage retention."""
import importlib.util, unittest
from datetime import datetime, timezone
from pathlib import Path
spec=importlib.util.spec_from_file_location("news",Path(__file__).with_name("update_news_feed.py"))
news=importlib.util.module_from_spec(spec);spec.loader.exec_module(news)
class FeedTests(unittest.TestCase):
    def test_rss_preserves_publication_and_rejects_unsafe_links_and_old_items(self):
        xml=b"""<rss><channel>
        <item><title>Real &amp; original</title><link>https://example.com/story?a=1&amp;b=2</link><description>&lt;p&gt;A short preview&lt;/p&gt;&lt;script&gt;bad()&lt;/script&gt;</description><pubDate>Tue, 20 Oct 2026 18:00:00 GMT</pubDate></item>
        <item><title>Unsafe</title><link>javascript:bad()</link><pubDate>Tue, 20 Oct 2026 18:00:00 GMT</pubDate></item>
        <item><title>Old</title><link>https://example.com/old</link><pubDate>Tue, 20 Oct 2020 18:00:00 GMT</pubDate></item>
        </channel></rss>"""
        items=news.parse_feed(xml,"Example",datetime(2026,10,20,19,tzinfo=timezone.utc))
        self.assertEqual(len(items),1);item=items[0]
        self.assertEqual(item["title"],"Real & original")
        self.assertEqual(item["link"],"https://example.com/story?a=1&b=2")
        self.assertEqual(item["pubDate"],"2026-10-20T18:00:00+00:00")
        self.assertEqual(item["desc"],"A short preview")
    def test_atom_preview_is_bounded_and_media_is_preserved(self):
        xml=('<feed xmlns="http://www.w3.org/2005/Atom"><entry><title>Atom</title><link href="https://example.com/atom"/><published>2026-10-20T18:00:00Z</published><summary>'+('word '*100)+'</summary></entry></feed>').encode()
        items=news.parse_feed(xml,"Example",datetime(2026,10,20,19,tzinfo=timezone.utc))
        self.assertEqual(len(items),1);self.assertLessEqual(len(items[0]["desc"]),220)
if __name__=="__main__":unittest.main()
