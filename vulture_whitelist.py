# Vulture whitelist for false positives
# These items are flagged as unused but are actually used in TYPE_CHECKING blocks
# or as type hints that vulture doesn't recognize.

# TYPE_CHECKING imports - vulture doesn't understand TYPE_CHECKING guards
# These are used for type hints but vulture sees them as unused
IThreadType  # noqa: F821 - Used in type hint line 63 of weaving_reporter.py
RepresentationLearner  # noqa: F821 - Used in type hints
