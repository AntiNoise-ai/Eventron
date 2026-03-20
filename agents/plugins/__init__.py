"""Agent plugins — each plugin is one sub-agent.

Import and register all plugins here for convenience.
"""

from agents.plugins.badge import BadgePlugin
from agents.plugins.change import ChangePlugin
from agents.plugins.checkin import CheckinPlugin
from agents.plugins.guide import GuidePlugin
from agents.plugins.identity import IdentityPlugin
from agents.plugins.organizer import OrganizerPlugin
from agents.plugins.pagegen import PagegenPlugin
from agents.plugins.planner import PlannerPlugin
from agents.plugins.seating import SeatingPlugin

ALL_PLUGINS = [
    IdentityPlugin,
    PlannerPlugin,
    OrganizerPlugin,
    SeatingPlugin,
    CheckinPlugin,
    ChangePlugin,
    BadgePlugin,
    PagegenPlugin,
    GuidePlugin,
]

__all__ = [
    "IdentityPlugin",
    "PlannerPlugin",
    "OrganizerPlugin",
    "SeatingPlugin",
    "CheckinPlugin",
    "ChangePlugin",
    "BadgePlugin",
    "PagegenPlugin",
    "GuidePlugin",
    "ALL_PLUGINS",
]
