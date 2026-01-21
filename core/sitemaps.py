from django.contrib.sitemaps import Sitemap
from django.urls import reverse

from .models import BlogPost


class StaticViewSitemap(Sitemap):
    """
    Sitemap for key static/marketing pages.
    
    This helps Google index the main public pages that describe DripEmails.org.
    """

    changefreq = "weekly"
    priority = 0.8

    def items(self):
        # Only include public, non-auth marketing/docs/tutorial pages.
        return [
            # Core marketing pages
            "core:home",
            "core:pricing",
            "core:about",
            "core:contact",
            "core:terms",
            "core:privacy",
            # Feature pages
            "core:feature_drip_campaigns",
            "core:feature_email_scheduling",
            "core:feature_analytics",
            "core:feature_subscriber_management",
            "core:feature_email_templates",
            # Docs / resources
            "core:resource_documentation",
            "core:resource_tutorials",
            "core:resource_api_reference",
            "core:resource_community",
            # Blog index
            "core:blog_index",
        ]

    def location(self, item):
        return reverse(item)


class BlogPostSitemap(Sitemap):
    """
    Sitemap for published blog posts stored in the BlogPost model.
    """

    changefreq = "weekly"
    priority = 0.7

    def items(self):
        return BlogPost.objects.filter(published=True)

    def lastmod(self, obj: BlogPost):
        # Use blog post date as last modified (simple but good enough for SEO here)
        return obj.date

