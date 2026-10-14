from synthride.server.bundle_builder import BundleBuilder
from synthride.server.game_server import GameServer
from synthride.server.html_page_builder import HtmlPageBuilder


def test_binds_and_reports_url():
    page, bundle = HtmlPageBuilder(), BundleBuilder()
    with GameServer(port=0, page_builder=page, bundle_builder=bundle) as server:
        assert server.url.startswith("http://127.0.0.1:")
        assert not server.url.endswith(":0/")
        assert server.page_builder is page
        assert server.bundle_builder is bundle
