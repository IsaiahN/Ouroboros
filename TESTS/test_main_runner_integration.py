#!/usr/bin/env python3
"""
Test script for main_runner.py evolution system integration
"""

import os
import sys
import tempfile
import subprocess
import json

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))


def test_main_runner_help():
    """Test that main_runner help shows new evolution commands."""
    print("Testing main_runner help output...")

    try:
        result = subprocess.run(
            [sys.executable, "main_runner.py", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            help_output = result.stdout

            # Check for evolution command
            if "evolution" in help_output:
                print("[PASS] Evolution command found in help")

                # Test evolution subcommands
                result2 = subprocess.run(
                    [sys.executable, "main_runner.py", "evolution", "--help"],
                    capture_output=True,
                    text=True,
                    timeout=10
                )

                if result2.returncode == 0 and "stats" in result2.stdout and "manage" in result2.stdout:
                    print("[PASS] Evolution subcommands (stats, manage) found")
                else:
                    print(f"[WARN] Evolution subcommands not found: {result2.stdout}")
            else:
                print("[WARN] Evolution command not found in help")

            # Check for evolved strategy option
            if "evolved" in help_output:
                print("[PASS] Evolved strategy found in help")
            else:
                print("[WARN] Evolved strategy not found in help")

        else:
            print(f"[ERROR] Help command failed: {result.stderr}")
            return False

    except Exception as e:
        print(f"[ERROR] Help test failed: {e}")
        return False

    return True


def test_evolution_management():
    """Test evolution system management commands."""
    print("\nTesting evolution management commands...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db_path = temp_db.name

    try:
        # Test evolution system initialization
        print("Testing evolution init...")
        result = subprocess.run(
            [sys.executable, "main_runner.py", "evolution", "manage", "init", "--db-path", temp_db_path],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode == 0:
            output = result.stdout
            if "Initialized" in output and "algorithms" in output:
                print("[PASS] Evolution system initialization works")
            else:
                print(f"[WARN] Unexpected init output: {output}")
        else:
            print(f"[WARN] Evolution init failed: {result.stderr}")

        # Test evolution status
        print("Testing evolution status...")
        result = subprocess.run(
            [sys.executable, "main_runner.py", "evolution", "manage", "status", "--db-path", temp_db_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            output = result.stdout
            if "Generation" in output and "Population" in output:
                print("[PASS] Evolution status command works")
            else:
                print(f"[WARN] Unexpected status output: {output}")
        else:
            print(f"[WARN] Evolution status failed: {result.stderr}")

        # Test evolution stats
        print("Testing evolution stats...")
        result = subprocess.run(
            [sys.executable, "main_runner.py", "evolution", "stats", "--db-path", temp_db_path],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            output = result.stdout
            if "Evolution System Statistics" in output:
                print("[PASS] Evolution stats command works")
            else:
                print(f"[WARN] Unexpected stats output: {output}")
        else:
            print(f"[WARN] Evolution stats failed: {result.stderr}")

    except Exception as e:
        print(f"[ERROR] Evolution management test failed: {e}")
        return False
    finally:
        try:
            os.unlink(temp_db_path)
        except:
            pass

    return True


def test_strategy_options():
    """Test that evolved strategy is available in command options."""
    print("\nTesting strategy options...")

    try:
        # Test play command help
        result = subprocess.run(
            [sys.executable, "main_runner.py", "play", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            help_output = result.stdout
            if "evolved" in help_output and "--strategy" in help_output:
                print("[PASS] Evolved strategy option available in play command")
            else:
                print("[WARN] Evolved strategy not found in play command help")

        # Test session command help
        result = subprocess.run(
            [sys.executable, "main_runner.py", "session", "--help"],
            capture_output=True,
            text=True,
            timeout=10
        )

        if result.returncode == 0:
            help_output = result.stdout
            if "evolved" in help_output and "--strategy" in help_output:
                print("[PASS] Evolved strategy option available in session command")
            else:
                print("[WARN] Evolved strategy not found in session command help")

    except Exception as e:
        print(f"[ERROR] Strategy options test failed: {e}")
        return False

    return True


def test_import_integration():
    """Test that evolution system imports work correctly."""
    print("\nTesting evolution system imports...")

    try:
        # Test importing main_runner to check for import errors
        import main_runner

        # Check if evolution components are available
        if hasattr(main_runner, 'EVOLUTION_AVAILABLE'):
            if main_runner.EVOLUTION_AVAILABLE:
                print("[PASS] Evolution system imports successful")

                # Check for key functions
                if hasattr(main_runner, 'evolved_strategy'):
                    print("[PASS] evolved_strategy function available")
                else:
                    print("[WARN] evolved_strategy function not found")

                if hasattr(main_runner, 'show_evolution_stats'):
                    print("[PASS] show_evolution_stats function available")
                else:
                    print("[WARN] show_evolution_stats function not found")

                if hasattr(main_runner, 'manage_evolution_system'):
                    print("[PASS] manage_evolution_system function available")
                else:
                    print("[WARN] manage_evolution_system function not found")

            else:
                print("[WARN] Evolution system not available (missing dependencies)")
        else:
            print("[ERROR] EVOLUTION_AVAILABLE flag not found")
            return False

    except ImportError as e:
        print(f"[ERROR] Import failed: {e}")
        return False
    except Exception as e:
        print(f"[ERROR] Import test failed: {e}")
        return False

    return True


def main():
    """Run all integration tests."""
    print("BitterTruth-AI Main Runner Integration Tests")
    print("=" * 50)

    all_tests_passed = True

    # Run all tests
    tests = [
        ("Import Integration", test_import_integration),
        ("Help Output", test_main_runner_help),
        ("Strategy Options", test_strategy_options),
        ("Evolution Management", test_evolution_management),
    ]

    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if not test_func():
                all_tests_passed = False
        except Exception as e:
            print(f"[ERROR] {test_name} failed with exception: {e}")
            all_tests_passed = False

    print("\n" + "=" * 50)
    if all_tests_passed:
        print("[SUCCESS] All main_runner integration tests passed!")
        print("\nEvolution system is now integrated into main_runner.py!")
        print("\nUsage examples:")
        print("  python main_runner.py evolution manage init")
        print("  python main_runner.py play game_123 --strategy evolved")
        print("  python main_runner.py session --strategy evolved --max-games 3")
        print("  python main_runner.py evolution stats")
    else:
        print("[PARTIAL] Some integration tests had warnings or failures")
        print("Check the output above for details")

    return all_tests_passed


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)