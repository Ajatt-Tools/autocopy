# Copyright: Ajatt-Tools and contributors; https://github.com/Ajatt-Tools
# License: GNU AGPL, version 3 or later; http://www.gnu.org/licenses/agpl.html

import pytest
from anki.collection import Collection
from aqt.qt import QApplication

from autocopy.main import html_to_clipboard_text


class TestHtmlToClipboardText:
    """Exercise real Qt parsing so clipboard formatting does not depend on mocked output."""

    @pytest.mark.parametrize(
        ("html", "expected"),
        [
            ("", ""),
            ("日本語", "日本語"),
            ("<b>日本語</b> <i>text</i>", "日本語 text"),
            ("one<br>two", "one\ntwo"),
            ("one<br/>two", "one\ntwo"),
            ("one<br><br>two", "one\n\ntwo"),
            ("one<br>", "one\n"),
            ("<div>one</div><div>two</div>", "one\ntwo"),
            ("<p>one</p><p>two</p>", "one\ntwo"),
            ("<div><b>日</b><br>本語</div>", "日\n本語"),
            ("<b>one<br>two", "one\ntwo"),
            ("one\ntwo", "one two"),
            ("<pre>one\ntwo</pre>", "one\ntwo"),
            ("&lt;b&gt;text&lt;/b&gt; &amp; &quot;quote&quot;", '<b>text</b> & "quote"'),
            ("A&nbsp;B", "A B"),
            ("A &amp;amp; B", "A &amp; B"),
            ("&lt;img src=x&gt;", "<img src=x>"),
            ("literal \ufffc character", "literal \ufffc character"),
            ("&#xfffc;", "\ufffc"),
            ("<br><br>", "\n\n"),
            ('<img src="picture.jpg">', ""),
            ("[sound:audio.mp3]", ""),
            ('one[sound:audio.mp3]<br><img src="picture.jpg">two', "one\ntwo"),
            ("&#91;sound:audio.mp3&#93;", "[sound:audio.mp3]"),
        ],
    )
    def test_conversion(self, qapp: QApplication, anki_collection: Collection, html: str, expected: str) -> None:
        """Strip media, preserve rendered breaks and literal text, and decode entities exactly once."""
        assert html_to_clipboard_text(html, media=anki_collection.media) == expected
