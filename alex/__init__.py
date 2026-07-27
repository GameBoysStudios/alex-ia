# -*- coding: utf-8 -*-
"""Paquete Alex: IA local en castellano, sin dependencias de LLMs externos."""

# Import perezoso para evitar ciclos al cargar submódulos.
def __getattr__(name):
    if name == "Alex":
        from alex.nucleo import Alex
        return Alex
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")

__all__ = ["Alex"]
