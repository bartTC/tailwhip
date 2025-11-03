"""Global context for config access."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from tailwhip.datatypes import Config

_config: Config | None = None


def set_config(config: Config) -> None:
    """Set the global config instance.

    Args:
        config: The Config instance to use globally

    """
    global _config
    _config = config


def get_config() -> Config:
    """Get the global config instance.

    Returns:
        The global Config instance

    Raises:
        RuntimeError: If config has not been initialized

    """
    if _config is None:
        raise RuntimeError("Config not initialized. Call set_config() first.")
    return _config
