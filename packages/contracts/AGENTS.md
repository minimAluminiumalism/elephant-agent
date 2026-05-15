# Contracts Package

This package owns shared records, schemas, IDs, and error codes.

## Rules

- keep it dependency-light and side-effect-free
- prefer additive evolution over breaking shape changes
- do not put runtime orchestration here

This package is the anti-collision layer for parallel module development.
