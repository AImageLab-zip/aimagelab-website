"""Small Python-Markdown extension for the wiki.

The editor preview (EasyMDE) renders GitHub-flavoured Markdown, the saved
page is rendered by Python-Markdown, which is not: `~~text~~` and task
lists showed correctly while editing and as literal characters once saved.
These two additions close that gap without a new dependency.

Enabled through MARKDOWNIFY["default"]["MARKDOWN_EXTENSIONS"].
"""
import re

from markdown.extensions import Extension
from markdown.inlinepatterns import SimpleTagInlineProcessor
from markdown.treeprocessors import Treeprocessor

_TASK = re.compile(r'^\[([ xX])\]\s+')


class _TaskListProcessor(Treeprocessor):
    """`- [ ] todo` / `- [x] done` -> a ballot box in front of the item."""

    def run(self, root):
        for li in root.iter('li'):
            # The item text is either directly in <li> or in its first <p>.
            holder = li
            if not (li.text or '').strip() and len(li) and li[0].tag == 'p':
                holder = li[0]
            match = _TASK.match(holder.text or '')
            if not match:
                continue
            box = '☑' if match.group(1).lower() == 'x' else '☐'
            holder.text = f'{box} ' + holder.text[match.end():]
            li.set('class', 'task-item')


class WikiExtension(Extension):
    def extendMarkdown(self, md):
        md.inlinePatterns.register(
            SimpleTagInlineProcessor(r'()~~(?!\s)(.+?)(?<!\s)~~', 'del'), 'wiki_del', 175)
        md.treeprocessors.register(_TaskListProcessor(md), 'wiki_tasks', 25)


def makeExtension(**kwargs):
    return WikiExtension(**kwargs)
