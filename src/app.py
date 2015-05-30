import phial

from docutils.core import publish_parts
import pystache
import datetime
from HTMLParser import HTMLParser
import info


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

    @classmethod
    def strip_tags(cls, html):
        s = cls()
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


def datetime_to_html_string(datetime):
    month = datetime.strftime("%B")

    day_suffix = "th"
    if not (11 <= datetime.day <= 13) and 1 <= datetime.day % 10 <= 3:
        day_suffix = {
            1: "st",
            2: "nd",
            3: "rd"
        }[datetime.day % 10]
    day = "{}<sup aria-hidden='true'>{}</sup>".format(str(datetime.day),
                                                      day_suffix)

    return "{} {}".format(month, day)


class Post(object):
    def __init__(self, post_file):
        frontmatter, content = phial.parse_frontmatter(post_file)

        # The path of the post file (ie: the RST file, not the result HTML
        # file).
        self.file_path = post_file.name

        self.title = frontmatter["title"]
        self.team = frontmatter["team"]
        self.published_on = (
                datetime.datetime.strptime(frontmatter["published_on"],
                                           "%B %d, %Y"))
        self.author = frontmatter["author"]
        self.raw_content = content

    def get_html_content(self):
        """Processes the raw content and returns HTML."""
        return render_rst(self.raw_content.read())

    def get_output_path(self):
        return phial.swap_extension(self.file_path, ".htm")

    def render_page(self, all_posts):
        def post_to_template_params(post):
            is_displayed_post = self.file_path == post.file_path
            params = {
                "title": post.title,
                "team_class":
                    "team-" + post.team.lower().replace(" ", "-"),
                "published_on_html":
                    datetime_to_html_string(post.published_on),
                "author": info.authors[post.author],
                "permalink": "/" + post.get_output_path(),
                "content_html": is_displayed_post and post.get_html_content(),
                "is_displayed_post": is_displayed_post,
            }
            return params

        template_params = {
            "displayed_post": post_to_template_params(self),
            "latest_posts": [post_to_template_params(i) for i in all_posts],
            "upcoming_post": info.upcoming_post,
        }
        template = phial.open_file("post-template.htm").read()
        return pystache.Renderer().render(template, template_params)


@phial.pipeline("posts/*.rst", binary_mode=False)
def posts(stream):
    all_posts = [Post(post_file) for post_file in stream.contents]
    all_posts.sort(reverse=True, key=lambda post: post.published_on)
    stream.prepare_contents()

    def post_to_file(post_file):
        post = Post(post_file)
        return phial.file(
            name=post.get_output_path(),
            content=post.render_page(all_posts),
            metadata=post)

    return stream | phial.map(post_to_file)


@phial.page(depends_on=posts)
def rss_feed():
    to_rss_string = lambda d: d.strftime("%a, %d %b %Y 11:00:00 GMT-8")
    sorted_posts = sorted(
        [i.metadata for i in phial.get_task(posts).files],
        reverse=True,
        key=lambda post: post.published_on)

    template_params = {
        "posts": [
            {
                "title": post.title,
                "path": post.get_output_path(),
                "date": to_rss_string(post.published_on),
            }
            for post in sorted_posts
        ]
    }
    template = phial.open_file("rss.xml").read()
    return phial.file(
        name="rss.xml",
        content=pystache.Renderer().render(template, template_params))


@phial.page(depends_on=posts)
def index():
    sorted_post_files = sorted(
        phial.get_task(posts).files,
        reverse=True,
        key=lambda phial_file: phial_file.metadata.published_on)
    latest_post_file = sorted_post_files[0]

    # Clone the latest post
    latest_post_file.seek(0)
    cloned_file = phial.file(name="index.htm", content=latest_post_file.read())

    return cloned_file


if __name__ == "__main__":
    phial.process()
