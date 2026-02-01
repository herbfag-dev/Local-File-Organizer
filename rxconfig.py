"""Reflex configuration file."""
import reflex as rx

config = rx.Config(
    app_name="local_file_organizer",
    db_url="sqlite:///reflex.db",
    disable_plugins=['reflex.plugins.sitemap.SitemapPlugin'],
)
