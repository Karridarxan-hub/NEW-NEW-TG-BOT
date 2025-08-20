# Handlers package initialization
from .main_handler import router as main_router
from .stats_handler import router as stats_router
from .match_handler import router as match_router
from .profile_handler import router as profile_router
from .settings_handler import router as settings_router
from .match_history_handler import router as match_history_router
from .form_analysis_handler import router as form_analysis_router
from .last_match_handler import router as last_match_router
from .current_match_handler import router as current_match_router
from .comparison_handler import router as comparison_router
from .help_handler import router as help_router

__all__ = ['main_router', 'stats_router', 'match_router', 'profile_router', 'settings_router', 'match_history_router', 'form_analysis_router', 'last_match_router', 'current_match_router', 'comparison_router', 'help_router']