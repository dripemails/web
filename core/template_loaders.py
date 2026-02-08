"""
Custom template loader for agent-specific templates.

When request has ?agent=<name> (e.g. agent=mobile), templates are looked up
under templates/agent/<name>/ first. If no agent or agent is blank, the full
normal template is used (default loader chain).

Compatible with Django 4.x and 5.x (uses django.template.Origin, no engine.origin).
"""
import os

from django.core.exceptions import SuspiciousFileOperation
from django.template import Origin, TemplateDoesNotExist
from django.template.loaders.base import Loader
from django.utils._os import safe_join

from core.middleware import get_current_request


class AgentTemplateLoader(Loader):
    """
    Tries agent-specific template path when request has ?agent= set.
    If agent is blank or unset, returns None so the normal template is used.
    """

    def get_template_sources(self, template_name):
        # Avoid recursion: when we're already loading an agent path, delegate
        if template_name.startswith("agent/"):
            return
        request = get_current_request()
        if not request:
            return
        agent = (request.GET.get("agent") or "").strip()
        if not agent:
            return
        template_dirs = getattr(self.engine, "dirs", None) or ()
        agent_template_name = f"agent/{agent}/{template_name}"
        for template_dir in template_dirs:
            try:
                name = safe_join(template_dir, agent_template_name)
            except SuspiciousFileOperation:
                continue
            if os.path.exists(name):
                yield Origin(
                    name=name,
                    template_name=agent_template_name,
                    loader=self,
                )
                return  # yield at most one (first found)

    def get_contents(self, origin):
        """Read template from filesystem (Origin.name is the absolute path)."""
        try:
            with open(origin.name, encoding=getattr(self.engine, "file_charset", "utf-8")) as f:
                return f.read()
        except FileNotFoundError:
            raise TemplateDoesNotExist(origin)
