from collections import defaultdict
from copy import deepcopy
from pathlib import Path
from typing import Any, DefaultDict, Dict, Optional, Union
from urllib.parse import quote

from loguru import logger
from mkdocs.commands.build import _build_page, _populate_page  # noqa: WPS450
from mkdocs.config import Config, config_options
from mkdocs.plugins import BasePlugin
from mkdocs.structure.files import File, Files
from mkdocs.structure.nav import Navigation, get_navigation
from mkdocs.structure.pages import Page


class Translator(BasePlugin):
    """Main plugin class."""

    config_scheme = (
        ("languages", config_options.Type(dict, required=True)),
        ("default_language", config_options.Type(str, required=True)),
        (
            "no_translation",
            config_options.Type(str, default="This page is not translated yet"),
        ),
    )

    def __init__(self) -> None:
        self.i18pages: DefaultDict[str, Files] = defaultdict(lambda: Files([]))
        self.i18navs: Dict[str, Navigation] = {}

    def on_nav(self, nav: Navigation, config: Config, files: Files) -> Navigation:
        """
        Handler for nav event.

        Builds navigation for translated pages.
        For each language creates it's own navigation.

        :param nav: current navigation.
        :param config: project config.
        :param files: all project files.
        :return: new Navigation.
        """
        if self.i18navs:
            return nav
        for language, lang_files in self.i18pages.items():
            logger.debug(f"Building navigation for {language}")
            self.i18navs[language] = get_navigation(lang_files, config)
            self.i18navs[language].homepage = deepcopy(
                self._get_lang_homepage(language),
            )
        return nav

    def on_files(self, files: Files, config: Config) -> Files:  # noqa: WPS210
        """
        Files event handler.

        It's called when MkDocs discovers all files.
        Here we filter all default pages and pages for translation.

        :param files: discovered files.
        :param config: mkdocs global config.
        :return: files for default language.
        """
        default_language = self.config.get("default_language")
        all_languages = set([default_language] + list(self.config["languages"]))

        # Idk we we need to process main_files separate from
        # translations, but it doesn't work without it.
        main_files = Files([])

        # Aux files, such as js or css.
        for aux_file in files:
            if aux_file not in files.documentation_pages():
                main_files.append(aux_file)
                for language in all_languages:
                    self.i18pages[language].append(aux_file)

        for page in files.documentation_pages():
            page_lang = self._get_lang(page)
            if page_lang == default_language:
                main_files.append(page)
            self.i18pages[page_lang].append(
                self.translate_page(page, Path(config.get("site_dir"))),
            )
        self._sort_translated_files()

        return main_files

    def translate_page(self, page: File, dest_dir: Path) -> File:
        """
        Create translated copy for the page.

        Creates a copy of a source page and modifies paths.
        For every page identifies the language
        and removes it from ulr and destination filename.

        For index pages also removes the "index.{page_lang}/" subdirectory
        from destination file path, and "index/" from url.

        :param page: page to translate.
        :param dest_dir: destination directory.
        :returns: "translated" page.
        """
        trans_page = deepcopy(page)
        page_lang = self._get_lang(trans_page)
        page_is_index = f"index.{page_lang}/" in trans_page.dest_path

        # Remove suffix from the page name.
        trans_page.name = trans_page.name.replace(f".{page_lang}", "")
        # If it's an index for subject.
        if page_is_index:
            trans_page.dest_path = trans_page.dest_path.replace(
                f"index.{page_lang}/",
                "",
            )
        else:
            trans_page.dest_path = trans_page.dest_path.replace(
                page.name,
                trans_page.name,
            )
        trans_page.dest_path = f"{page_lang}/{trans_page.dest_path}"
        trans_page.abs_dest_path = str(dest_dir / trans_page.dest_path)
        # If it's a main index page for language.
        if trans_page.url == ".":
            trans_page.url = f"{page_lang}/"
        else:
            trans_page.url = f"{page_lang}/{trans_page.url}"

        trans_page.url = trans_page.url.replace(
            quote(page.name),
            quote(trans_page.name),
        )

        if trans_page.url.endswith("index/"):
            trans_page.url = trans_page.url.replace(
                "index/",
                "",
            )
        return trans_page

    def on_page_context(
        self,
        context: Dict[str, Any],
        page: Page,
        config: Config,
        nav: Navigation,
    ) -> Dict[str, Any]:
        """
        Mkdocs-material search context support for translations.

        Identifies page language and sets current language in
        material theme config.

        :param context: page context.
        :param page: current page.
        :param config: global mkdocs config.
        :param nav: page navigation.
        :return: modified page context.
        """
        for language in self.config.get("languages"):
            if page.url.startswith(f"{language}/"):
                if config["theme"].name == "material":
                    context["config"]["theme"].language = language
                break
        return context

    def on_post_build(self, config: Config) -> None:
        """
        Post build event handler.

        Populates and builds pages with navigation for each translation.

        :param config: mkdocs global config.
        """
        logger.info("Building translations.")
        for language in self.config.get("languages"):
            logger.info(f"Building {language} documentation")

            files = self.i18pages[language]
            nav = config["plugins"].run_event(
                "nav",
                self.i18navs[language],
                config=config,
                files=files,
            )

            # Cycles are separated cause at first we need to populate all pages.
            for populate_page in files.documentation_pages():
                _populate_page(populate_page.page, config, files, dirty=False)

            for build_page in self.i18pages[language].documentation_pages():
                _build_page(
                    build_page.page,
                    config,
                    files,
                    nav,
                    env=config["theme"].get_env(),
                    dirty=False,
                )

    def _get_lang(self, page: Union[Page, File]) -> str:
        """
        Get page language based on name.

        :param page: target page.
        :returns: detected language.
        """
        lang = page.url.rsplit(".", 1)[-1].strip("/")
        if lang in self.config.get("languages", {}):
            return str(lang)
        return str(self.config.get("default_language"))

    def _get_lang_homepage(self, language: str) -> Optional[File]:
        for page in self.i18pages[language]:
            if page.url == f"{language}/":
                return page
        return None

    def _sort_translated_files(self) -> None:
        """Sort all translated pages based on their path."""

        def sort_key(page_file: File) -> int:
            """
            Finds url's path length.

            :param page_file: file to check.
            :return: length of file's url.
            """
            return len(page_file.url.split("/"))

        for key, pages in self.i18pages.items():
            self.i18pages[key] = Files(sorted(pages, key=sort_key))
