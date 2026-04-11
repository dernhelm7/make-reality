"""Labyrinth static site generator."""

from .builder import BuildError, BuildResult, build_site

__all__ = ["BuildError", "BuildResult", "build_site"]
