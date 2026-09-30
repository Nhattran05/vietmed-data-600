# -*- coding: utf-8 -*-
"""
vietmed_e2e/validators
Bộ kiểm định tính nhất quán hồ sơ lâm sàng (Profile Consistency Validator).
"""

from vietmed_e2e.validators.consistency_validator import validate_profiles, ValidationResult

__all__ = ["validate_profiles", "ValidationResult"]
