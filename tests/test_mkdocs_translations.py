from mkdocs.structure.files import File

from mkdocs_translations.plugin import Translator


def test_stub() -> None:
    """Test stub (Replace later)."""
    magic_value = 1
    assert magic_value == 1


def test_pages_sort() -> None:
    """Test i18pages sort correctness."""
    plugin = Translator()
    test_lang = "test"
    index_page = File("/tmp/theme/index.md", "/tmp", "/tmp", use_directory_urls=False)
    index_page.url = "lang/theme/"

    second = File("/tmp/theme/b.md", "/tmp", "/tmp", use_directory_urls=False)
    second.url = "lang/theme/b/"
    plugin.i18pages[test_lang].append(
        second,
    )
    plugin.i18pages[test_lang].append(
        index_page,
    )
    plugin._sort_translated_files()
    doc_pages = plugin.i18pages[test_lang].documentation_pages()
    assert doc_pages[0] == index_page
