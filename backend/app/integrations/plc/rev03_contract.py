"""Contrato oficial Rev.03.

O módulo Rev.02 permanece como implementação/alias durante a janela de
compatibilidade para não quebrar extensões já instaladas.
"""
from .rev02_contract import (  # noqa: F401
    FEATURE_FLAGS,
    READER_RESULTS,
    READER_STATES,
    RECIPES,
    decode_features,
    decode_reader_block,
    decode_reader_snapshot,
    get_rev03_diagnostic,
    sample_reader_registers,
)

__all__ = [
    "FEATURE_FLAGS", "READER_RESULTS", "READER_STATES", "RECIPES",
    "decode_features", "decode_reader_block", "decode_reader_snapshot",
    "get_rev03_diagnostic", "sample_reader_registers",
]
