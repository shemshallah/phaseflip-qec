# 📄 FILE 22: phaseflip_qec/benchmarks/__init__.py

**Filename:** `phaseflip_qec/benchmarks/__init__.py`  
**Purpose:** Benchmarking module initialization  
**Location:** `phaseflip_qec/benchmarks/` directory

"""
PhaseFlip QEC Benchmarking Suite

Provides comprehensive performance benchmarking and validation tools.
"""

from .error_suppression import (
    ErrorSuppressionBenchmark,
    run_full_benchmark_suite,
    compare_with_other_codes,
)

__all__ = [
    "ErrorSuppressionBenchmark",
    "run_full_benchmark_suite",
    "compare_with_other_codes",
]