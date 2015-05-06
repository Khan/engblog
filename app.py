import phial

from docutils.core import publish_parts
import pystache
import datetime
import copy
from HTMLParser import HTMLParser


class MLStripper(HTMLParser):
    """Class to help strip markup from a string.

    See http://stackoverflow.com/a/925630/3920202.
    """

    def __init__(self):
        self.reset()
        self.fed = []

    def handle_data(self, d):
        self.fed.append(d)

    def get_data(self):
        return ''.join(self.fed)


def strip_tags(html):
    s = MLStripper()
    s.feed(html)
    return s.get_data()


def render_rst(text):
    """Renders some restructured text and returns generated HTML."""

    docutils_settings = {
        # I don't want <h1> tags in the post
        "initial_header_level": 2,

        # I don't want the docutils class added to every element
        "strip_classes": "docutils",

        "syntax_highlight": "short"
    }
    post_body = (
        publish_parts(
            text,
            writer_name="html",
            settings_overrides=docutils_settings)["html_body"])

    return post_body


@phial.page(["posts/*.rst"])
def post_page(source_file):
    template = phial.open_file("posts-template.htm").read()

    frontmatter, content = phial.parse_frontmatter(source_file)

    # Use docutils to render the restructured text
    post_body = render_rst(content.read())

    # Use mustache to plug everything into the template
    renderer = pystache.Renderer()
    content = renderer.render(
        template,
        frontmatter,
        {
            "body": post_body,
            "stripped_description":
                strip_tags(render_rst(frontmatter["description"]))
        })

    return phial.file(
        name=phial.swap_extension(source_file.name, ".htm"),
        content=content,
        metadata=frontmatter or {})


def render_index_page(template_path, metadata_transformer=None,
                      extra_template_values=None):
    """Renders an index-like page using the given template."""
    template = phial.open_file(template_path)

    def date_from_file(f):
        return datetime.datetime.strptime(f.metadata["date"], "%B %d, %Y")

    sorted_posts = sorted(phial.get_task(post_page).files, reverse=True,
                          key=date_from_file)

    # Get the metadata ready
    posts_metadata = [copy.deepcopy(i.metadata) for i in sorted_posts]
    for metadata, post in zip(posts_metadata, sorted_posts):
        metadata["team_id"] = (
            metadata.get("team", "").strip().replace(" ", "-").lower())
        metadata["description"] = render_rst(metadata["description"])
        metadata["link"] = post.name

    if metadata_transformer:
        posts_metadata = [metadata_transformer(i) for i in posts_metadata]

    # Use mustache to plug everything into the template
    renderer = pystache.Renderer()
    content = renderer.render(
        template.read(),
        {"posts": [i for i in posts_metadata if not i.get("is_draft", False)]},
        extra_template_values or {})

    return phial.file(name=template_path, content=content)


@phial.page(depends_on=post_page)
def main_page():
    return render_index_page("index.htm")


@phial.page(depends_on=post_page)
def rss_feed():
    def metadata_transformer(metadata):
        metadata["description"] = strip_tags(metadata["description"])

        date = datetime.datetime.strptime(metadata["date"], "%B %d, %Y")
        # Sat, 07 Sep 2002 0:00:01 GMT
        metadata["date"] = date.strftime("%a, %d %b %Y 0:00:01 GMT-8")

        return metadata

    return render_index_page("rss.xml", metadata_transformer)


if __name__ == "__main__":
    phial.process()
