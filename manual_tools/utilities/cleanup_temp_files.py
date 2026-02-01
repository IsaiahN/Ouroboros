import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache

#!/usr/bin/env python3
"""
Temporary File Cleanup System
Automatically removes temporary diagnostic/analysis files on startup.

INTEGRATION: This script runs automatically at the start of every evolution run
via run_evolution.py to keep the workspace clean.

Manual usage:
    python cleanup_temp_files.py              # Delete temp files
    python cleanup_temp_files.py --dry-run    # Preview what would be deleted
"""

import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'  # Rule 1: Disable pycache
import logging
import subprocess
from pathlib import Path

logger = logging.getLogger(__name__)

# Patterns for temporary files (case-insensitive matching)
TEMP_PATTERNS = [
    "check_*.py",
    "investigate_*.py", 
    "analyze_*.py",
    "diagnose_*.py",
    "show_*.py",
    "run_arc_debug_*.py",
    "run_arc_game_*.py",
    "detailed_*.py",
    "verify_*.py",
    "find_*.py",
    "debug_*.py",        # Debug scripts
    "quick_*.py",        # Quick check scripts
    "fix_*.py",          # One-time fix scripts
    "temp_*.py",         # Temp files
    "*_summary.*",       # Cleanup summary files (all extensions, case-insensitive)
    "*_SUMMARY.*",       # Explicit uppercase variant
    "*_analysis.py",     # Analysis scripts
    "*_report.py",       # Report scripts
    "*_check.py",        # Check scripts
    "BugFix_*.*",        # BugFix files with any extension
    "*.log",             # Log files (Rule 2: Database-only storage)
    "*.txt"              # Text report files (temporary analysis outputs)
]

# Files to KEEP (whitelist - never delete these)
# NOTE: Files in /tests and /manual_tools are protected by SKIP_DIRS
# NOTE: manual_tools/*.py are protected by SKIP_DIRS but listed here for documentation:
#   - gameplay_analyzer.py: Reusable gameplay progression analysis tool
#   - schema_inspector.py: Reusable database schema inspection tool
KEEP_FILES = {
    # TIER 1: Core System Files (imported by core_gameplay.py or autonomous_evolution_runner.py)
    "database_interface.py",
    "core_gameplay.py",
    "autonomous_evolution_runner.py",
    "arc_api_client.py",
    "game_session_manager.py",
    "action_handler.py",
    "database_logger.py",
    "prestige_engine.py",
    "evolutionary_engine.py",
    "horizontal_transfer_engine.py",
    "viral_package_engine.py",
    "rule_induction_engine.py",
    "network_intelligence_engine.py",
    "regulatory_signal_engine.py",
    "collective_reasoning_engine.py",
    "sensation_engine.py",
    "sequence_abstraction.py",
    "sequence_pruning_system.py",
    "performance_analyzer.py",
    "lessons_learned_engine.py",
    "near_miss_analyzer.py",
    "frustration_detector.py",
    "agent_operating_mode_system.py",
    "agent_self_model.py",
    "arc_rlvr_framework.py",
    
    # TIER 2: Active Utilities (referenced by core files)
    "breakthrough_budget_allocator.py",
    "breakthrough_detector.py",
    "multi_stage_matching_pipeline.py",
    "subgoal_planning_activator.py",
    "subgoal_planner.py",
    "automated_assessment_runner.py",
    "revive_agents.py",
    "evolution_with_parasites.py",
    "agent_factory.py",
    "agent_lifecycle_manager.py",
    "game_scheduler.py",
    "visual_analyzer.py",
    "object_detector.py",
    "optimization_threshold_system.py",
    "somatic_profile_system.py",
    "game_diversity_preservation.py",
    "meta_learning_curriculum.py",
    "prestige_parasite_detector.py",
    "abstraction_config.py",
    "abstraction_schema.py",
    "adaptive_action_limits.py",
    "api_reset_strategy.py",
    "run_evolution.py",
    "schema_auto_maintenance.py",
    "ouroboros_coordinator.py",
    "evolution_game_scheduler.py",
    "enhanced_database_interface.py",
    "disk_space_monitor.py",
    "safe_cleanup.py",
    "cleanup_temp_files.py",
    "requirements.txt",
    
    # TIER 3: Experimental/Future (kept in root but not integrated)
    "symbolic_reasoning_engine.py",
    "visual_reasoning_engine.py",
    "emotional_gameplay_mixin.py",
    "specialist_coordinator.py",
    
    # Package init
    "__init__.py",
    
    # Documentation (keep)
    "README.md",
    "CODEBASE_INVENTORY.md",
}

# Directories to skip (but we'll delete __pycache__ folders entirely)
SKIP_DIRS = {
    ".git",
    ".vscode",
    ".venv",
    "venv",
    "env",
    "tests",           # Unit test files - never delete
    "manual_tools",    # Manual utility scripts - never delete
    "migrations",      # Database migrations - never delete
    "DOCS",            # Documentation - never delete
    "experimental",    # Future feature experiments - never delete
}

# Note: __pycache__ is NOT in SKIP_DIRS because we want to DELETE those folders entirely


def _load_tracked_files(repo_root: Path) -> set[str]:
    """Return git-tracked file paths relative to repo root."""
    try:
        result = subprocess.run(
            ["git", "ls-files"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return {line.strip() for line in result.stdout.splitlines() if line.strip()}
    except Exception:
        return set()

def should_delete(filepath: Path) -> bool:
    """
    Determine if file should be deleted.
    
    Rules:
    1. If in whitelist, keep it
    2. If ALL_CAPS.md file (LLM-generated docs), delete it (case-sensitive check)
    3. If matches temp pattern (case-insensitive), delete it
    4. Otherwise, keep it
    """
    filename = filepath.name
    
    # Whitelist check
    if filename in KEEP_FILES:
        return False
    
    # Check for ALL_CAPS.md files (LLM-generated documentation) - CASE SENSITIVE
    if filename.endswith('.md'):
        # Get filename without extension
        name_without_ext = filename[:-3]
        # Must contain at least one underscore (multi-word pattern like FILE_NAME.md)
        # All letters must be uppercase (no lowercase allowed)
        # Excludes single-word files like "README.md"
        has_underscore = '_' in name_without_ext
        has_letter = any(c.isalpha() for c in name_without_ext)
        has_lowercase = any(c.islower() for c in name_without_ext)
        if has_underscore and has_letter and not has_lowercase:
            # Verify all alphabetic characters are uppercase
            letters_only = ''.join(c for c in name_without_ext if c.isalpha())
            if letters_only and letters_only.isupper():
                return True
    
    # Pattern check (case-insensitive)
    filename_lower = filename.lower()
    for pattern in TEMP_PATTERNS:
        pattern_lower = pattern.lower()
        
        # Simple wildcard matching
        if pattern_lower.count("*") == 2:
            # Pattern like *_summary.* - split into prefix, middle, suffix
            parts = pattern_lower.split("*")
            # parts = ["", "_summary.", ""] for *_summary.*
            if len(parts) == 3:
                prefix, middle, suffix = parts
                # Check if middle part is in filename at the right position
                if middle in filename_lower:
                    idx = filename_lower.find(middle)
                    # If prefix is empty (starts with *), just check middle is there
                    # If suffix is empty (ends with *), just check middle is there
                    if (not prefix or filename_lower.startswith(prefix)):
                        if (not suffix or filename_lower[idx + len(middle):].endswith(suffix)):
                            return True
        elif pattern_lower.startswith("*"):
            if filename_lower.endswith(pattern_lower[1:]):
                return True
        elif pattern_lower.endswith("*"):
            if filename_lower.startswith(pattern_lower[:-1]):
                return True
        elif "*" in pattern_lower:
            prefix, suffix = pattern_lower.split("*", 1)
            if filename_lower.startswith(prefix) and filename_lower.endswith(suffix):
                return True
        elif filename_lower == pattern_lower:
            return True
    
    return False

def cleanup_temp_files(
    workspace_root: str = ".",
    allow_tracked: bool = False,
    git_rm: bool = False,
    tracked_files: set[str] | None = None,
) -> tuple[int, int]:
    """
    Clean up temporary files and __pycache__ folders from workspace.
    
    Returns:
        (files_deleted, bytes_freed)
    """
    workspace_path = Path(workspace_root)
    tracked_files = tracked_files if tracked_files is not None else _load_tracked_files(workspace_path)
    files_deleted = 0
    bytes_freed = 0
    pycache_folders_deleted = 0
    skip_tracked_count = 0
    
    print("\n[CLEANUP] Removing temporary files and __pycache__ folders...")
    print("=" * 80)
    
    # Walk workspace
    for root, dirs, files in os.walk(workspace_path):
        root_path = Path(root)
        
        # Delete __pycache__ folders entirely
        if '__pycache__' in dirs:
            pycache_path = root_path / '__pycache__'
            try:
                # Count files in __pycache__ before deleting
                pycache_size = sum(f.stat().st_size for f in pycache_path.rglob('*') if f.is_file())
                pycache_file_count = sum(1 for f in pycache_path.rglob('*') if f.is_file())
                
                # Delete the entire folder
                import shutil
                shutil.rmtree(pycache_path)
                
                files_deleted += pycache_file_count
                bytes_freed += pycache_size
                pycache_folders_deleted += 1
                print(f"  [DEL] {pycache_path.relative_to(workspace_path)}/ ({pycache_file_count} files)")
            except Exception as e:
                logger.warning(f"Failed to delete {pycache_path}: {e}")
            
            # Remove from dirs so we don't walk into it
            dirs.remove('__pycache__')
        
        # Skip certain directories (but we'll check individual files)
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        

        
        for filename in files:
            filepath = root_path / filename
            
            # Process Python files, markdown files, log files, text files, and summary files (case-insensitive)
            filename_lower = filename.lower()
            if not (filename_lower.endswith(".py") or filename_lower.endswith(".md") or filename_lower.endswith(".log") or filename_lower.endswith(".txt") or "_summary." in filename_lower):
                continue
            
            # Skip DOCS directory for Python files, but allow .md files to be cleaned there
            if "DOCS" in filepath.parts and filename_lower.endswith(".py"):
                continue
            
            rel_path = filepath.relative_to(workspace_path)
            rel_posix = rel_path.as_posix()
            is_tracked = rel_posix in tracked_files

            if is_tracked and not (allow_tracked or git_rm):
                skip_tracked_count += 1
                continue

            if should_delete(filepath):
                try:
                    file_size = filepath.stat().st_size
                    if git_rm and is_tracked:
                        result = subprocess.run(
                            ["git", "rm", "--quiet", rel_posix],
                            cwd=workspace_path,
                            capture_output=True,
                        )
                        if result.returncode != 0:
                            logger.warning(f"git rm failed for {rel_path}: {result.stderr}")
                            continue
                    else:
                        filepath.unlink()
                    files_deleted += 1
                    bytes_freed += file_size
                    prefix = "[GIT RM]" if git_rm and is_tracked else "[DEL]"
                    print(f"  {prefix} {rel_path}")
                except Exception as e:
                    logger.warning(f"Failed to delete {filepath}: {e}")
    
    print("=" * 80)
    if pycache_folders_deleted > 0:
        print(f"[OK] Deleted {files_deleted} files + {pycache_folders_deleted} __pycache__ folders ({bytes_freed / 1024:.1f} KB freed)\n")
    else:
        print(f"[OK] Deleted {files_deleted} files ({bytes_freed / 1024:.1f} KB freed)\n")

    if skip_tracked_count > 0:
        print(f"[SKIP] {skip_tracked_count} tracked file(s) protected (suppressed detail)")
    
    return files_deleted, bytes_freed

def list_temp_files(
    workspace_root: str = ".",
    tracked_files: set[str] | None = None,
    allow_tracked: bool = False,
) -> list[Path]:
    """
    List temporary files without deleting them.
    Useful for dry-run before cleanup.
    """
    workspace_path = Path(workspace_root)
    tracked_files = tracked_files if tracked_files is not None else _load_tracked_files(workspace_path)
    temp_files = []
    
    for root, dirs, files in os.walk(workspace_path):
        dirs[:] = [d for d in dirs if d not in SKIP_DIRS]
        root_path = Path(root)
        
        for filename in files:
            filepath = root_path / filename
            filename_lower = filename.lower()
            
            if not (filename_lower.endswith(".py") or filename_lower.endswith(".md") or filename_lower.endswith(".log") or filename_lower.endswith(".txt") or "_summary." in filename_lower):
                continue
            
            # Skip DOCS directory for Python files, but allow .md files to be cleaned there
            if "DOCS" in filepath.parts and filename_lower.endswith(".py"):
                continue
            
            rel_posix = filepath.relative_to(workspace_path).as_posix()
            is_tracked = rel_posix in tracked_files
            if is_tracked and not allow_tracked:
                continue

            if should_delete(filepath):
                temp_files.append(filepath)
    
    return temp_files

if __name__ == "__main__":
    import sys
    
    # Parse arguments
    dry_run = "--dry-run" in sys.argv or "-n" in sys.argv
    allow_tracked = "--allow-tracked" in sys.argv
    git_rm = "--git-rm" in sys.argv

    if git_rm:
        allow_tracked = True

    tracked_files = _load_tracked_files(Path("."))
    
    if dry_run:
        print("\n[DRY RUN] Files that would be deleted:")
        print("=" * 80)
        temp_files = list_temp_files(tracked_files=tracked_files, allow_tracked=allow_tracked)
        for filepath in temp_files:
            print(f"  {filepath}")
        print("=" * 80)
        print(f"Total: {len(temp_files)} files\n")
    else:
        cleanup_temp_files(allow_tracked=allow_tracked, git_rm=git_rm, tracked_files=tracked_files)
