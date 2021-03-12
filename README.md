# Mkdocs translations plugin

This plugin is inspired by [mkdocs-static-i18n](https://github.com/ultrabug/mkdocs-static-i18n) plugin,
but it solves problem with tabs. With it, you can use nested documentation file structure.

Also, it's integrated with mkdocs-material theme features.
Such as [search](https://squidfunk.github.io/mkdocs-material/setup/setting-up-site-search/),
[language switcher](https://squidfunk.github.io/mkdocs-material/setup/changing-the-language/),
and [tabs](https://squidfunk.github.io/mkdocs-material/setup/setting-up-navigation/#navigation-tabs).

For example, with the following configuration:
```yaml
# Add this plugin in your mkdocs.yml
plugins:
  - translations:
      default_language: ru
      languages:
        en: english
        ru: русский
```

It will turn this.
```
docs
├── Dir1
│   ├── index.md
│   ├── index.en.md
│   ├── Theme1.md
│   ├── Theme1.en.md
│   ├── Theme2.md
│   └── Theme2.en.md
├── index.en.md
├── index.md
└── Dir2
    ├── index.md
    ├── index.en.md
    ├── Theme1.md
    └── Theme1.en.md
```

Into this:
```
site
├── 404.html
├── index.html
├── Dir1
│   ├── Theme1
│   │   └── index.html
│   ├── index.html
│   └── Theme2
│       └── index.html
├── Dir2
│   ├── Theme1
│   │   └── index.html
│   └── index.html
├── en
│   ├── Dir1
│   │   ├── Theme1
│   │   │   └── index.html
│   │   ├── index.html
│   │   └── Theme2
│   │       └── index.html
│   ├── index.html
│   └── Dir2
│       ├── Theme1
│       │   └── index.html
│       └── index.html
└── ru
    ├── Dir1
    │   ├── Theme1
    │   │   └── index.html
    │   ├── index.html
    │   └── Theme2
    │       └── index.html
    ├── index.html
    └── Dir2
        ├── Theme1
        │   └── index.html
        └── index.html
```
