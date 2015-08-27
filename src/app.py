"""A script that builds the blog's content.

Run this with `python app.py output_dir`.
"""

import os
import sys
import glob

import pystache

import info
from post import Post

POST_TEMPLATE = open("post-template.htm", "rb").read().decode("utf-8")
RSS_TEMPLATE = open("rss-template.xml", "rb").read().decode("utf-8")


def render_post_page(posts, current_post_index):
    """Renders a single post page.

    Arguments:
        posts - A list of Post objects sorted by published date.
        current_post_index - The index of the current post in the list of
            posts.

    Returns: A string or unicode object containing the rendered page.
    """
    def get_post_dict(index):
        if 0 < index < len(posts):
            return posts[index].to_dict()

        return None

    template_params = {
        "posts": [post.to_dict() for post in posts],
        "displayed_post": get_post_dict(current_post_index),
        "html_content": posts[current_post_index].get_html_content(),
        "next_post": get_post_dict(current_post_index - 1),
        "previous_post": get_post_dict(current_post_index + 1),
        "upcoming_post": info.upcoming_post,
    }
    renderer = pystache.Renderer(missing_tags="strict")
    return renderer.render(POST_TEMPLATE, template_params)


def render_rss_page(posts):
    """Renders the RSS feed.

    Arguments:
        posts - A list of Post objects sorted by published date.

    Returns: A string or unicode object containing the rendered page.
    """
    to_rss_string = lambda d: d.strftime("%a, %d %b %Y 11:00:00 GMT-8")

    template_params = {
        "posts": [
            {
                "title": post.title,
                "relative_href": "posts/" + post.get_output_name(),
                "date": to_rss_string(post.published_on),
            }
            for post in posts
        ]
    }
    renderer = pystache.Renderer(missing_tags="strict")
    return renderer.render(RSS_TEMPLATE, template_params)


def main(output_directory):
    # Grab all of the posts and sort them by their published date
    posts = [Post(path) for path in glob.glob("posts/*")]
    posts = sorted(posts, reverse=True, key=lambda post: post.published_on)

    # Make a posts directory in our output directory
    os.mkdir(os.path.join(output_directory, "posts"))

    # Go through and create all the post pages
    for index, post in enumerate(posts):
        output_path = os.path.join(output_directory, "posts",
                                   post.get_output_name())
        rendered_post = render_post_page(posts, index)

        with open(output_path, "wb") as f:
            f.write(rendered_post.encode("utf-8"))

        # If this is the current post, we also make it the index page
        if index == 0:
            with open(os.path.join(output_directory, "index.htm"), "wb") as f:
                f.write(rendered_post.encode("utf-8"))

    # Create the RSS feed
    with open(os.path.join(output_directory, "rss.xml"), "wb") as f:
        f.write(render_rss_page(posts).encode("utf-8"))

if __name__ == "__main__":
    main(sys.argv[1])
