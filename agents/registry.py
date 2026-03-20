"""Plugin registry — dynamic sub-agent discovery and routing prompt generation.

The orchestrator NEVER hard-codes agent names. It uses the registry to
dynamically discover available plugins and build the intent classification prompt.
"""

from __future__ import annotations

from agents.plugins.base import AgentPlugin


class PluginRegistry:
    """Registry for agent plugins. Thread-safe for read-heavy workloads."""

    def __init__(self):
        self._plugins: dict[str, AgentPlugin] = {}

    def register(self, plugin: AgentPlugin) -> None:
        """Register a plugin. Overwrites any existing plugin with the same name."""
        self._plugins[plugin.name] = plugin

    def unregister(self, name: str) -> bool:
        """Remove a plugin by name. Returns True if found."""
        return self._plugins.pop(name, None) is not None

    def get(self, name: str) -> AgentPlugin | None:
        """Look up a plugin by name."""
        return self._plugins.get(name)

    @property
    def active_plugins(self) -> list[AgentPlugin]:
        """List all enabled plugins."""
        return [p for p in self._plugins.values() if p.enabled]

    @property
    def all_plugins(self) -> list[AgentPlugin]:
        """List all registered plugins (including disabled)."""
        return list(self._plugins.values())

    def build_routing_prompt(self) -> str:
        """Dynamically build the intent classification prompt
        based on currently active plugins.

        Returns a multi-line string listing each plugin's name,
        description, and keywords.
        """
        if not self.active_plugins:
            return "No plugins available. Respond as a general assistant."

        lines = []
        for p in self.active_plugins:
            keywords = ", ".join(p.intent_keywords)
            lines.append(f"- {p.name}: {p.description} (keywords: {keywords})")
        return "\n".join(lines)

    def get_identity_required_plugins(self) -> list[str]:
        """Get names of plugins that require user identity."""
        return [p.name for p in self.active_plugins if p.requires_identity]
