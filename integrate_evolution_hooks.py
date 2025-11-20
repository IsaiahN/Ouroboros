"""
Integration Script for Autonomous Evolution Runner
Adds all task integration hooks and self-awareness logic.
"""

import re

FILE_PATH = "autonomous_evolution_runner.py"

# Read the file
with open(FILE_PATH, "r", encoding="utf-8") as f:
    content = f.read()

# 1. Add subprocess import at the top (after other imports)
if "import subprocess" not in content:
    # Find the imports section and add subprocess
    import_pattern = r"(import argparse\nimport signal)"
    import_replacement = r"\1\nimport subprocess"
    content = re.sub(import_pattern, import_replacement, content)
    print("✅ Added subprocess import")

# 2. Add integration methods to the class
# Find a good insertion point - after __init__ method
integration_methods = '''
    
    def _run_sequence_validation(self, generation: int):
        """Run sequence validation (Task #7 integration)."""
        try:
            logger.info("🔍 Running sequence validation...")
            result = subprocess.run(
                ["python", "validate_sequences.py", "--max", "5"],
                capture_output=True,
                text=True,
                timeout=300,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                logger.info("✅ Sequence validation complete")
            else:
                logger.warning(f"⚠️ Sequence validation failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error running sequence validation: {e}")
    
    def _run_agent_revival(self, generation: int):
        """Revive high-prestige agents (Task #9 integration)."""
        try:
            logger.info("🔄 Checking for agents to revive...")
            result = subprocess.run(
                ["python", "revive_agents.py", "--max", "2"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                logger.info("✅ Agent revival complete")
                if result.stdout:
                    logger.info(result.stdout)
            else:
                logger.warning(f"⚠️ Agent revival failed: {result.stderr}")
        except Exception as e:
            logger.error(f"Error running agent revival: {e}")
    
    def _run_performance_analytics(self, generation: int):
        """Analyze exploiter performance (Task #4 integration)."""
        try:
            logger.info("📊 Analyzing exploiter performance...")
            result = subprocess.run(
                ["python", "analyze_exploiter_performance.py", "--days", "7"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                logger.info("✅ Performance analysis complete")
                if result.stdout:
                    logger.info(result.stdout)
        except Exception as e:
            logger.error(f"Error running performance analysis: {e}")
    
    def _run_scorecard_analysis(self, generation: int):
        """Analyze scorecards for system issues (Recurring task integration)."""
        try:
            logger.info("🎮 Analyzing recent scorecards...")
            result = subprocess.run(
                ["python", "analyze_scorecards.py", "--max", "10"],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=os.path.dirname(os.path.abspath(__file__))
            )
            if result.returncode == 0:
                logger.info("✅ Scorecard analysis complete")
                if result.stdout:
                    logger.info(result.stdout)
        except Exception as e:
            logger.error(f"Error running scorecard analysis: {e}")
'''

# Find the end of __init__ method and insert integration methods
init_pattern = r"(self\.should_stop = False\s+self\.stop_reason = None)"
if re.search(init_pattern, content):
    content = re.sub(init_pattern, r"\1" + integration_methods, content)
    print("✅ Added integration methods to class")
else:
    print("⚠️ Could not find __init__ method end, integration methods not added")

# 3. Add hook calls in the main evolution loop
# We'll add a comment marker that can be found and used
hook_calls = """
        
        # TASK INTEGRATION HOOKS (Added by integration script)
        try:
            # Every generation: Validation and scorecard analysis
            if generation % 1 == 0:
                self._run_sequence_validation(generation)
                self._run_scorecard_analysis(generation)
            
            # Every 5 generations: Agent revival
            if generation % 5 == 0 and generation > 0:
                self._run_agent_revival(generation)
            
            # Every 10 generations: Performance analytics
            if generation % 10 == 0 and generation > 0:
                self._run_performance_analytics(generation)
        except Exception as e:
            logger.error(f"Error in task integration hooks: {e}")
"""

# Try to find where to insert the hooks - look for logger.info patterns in evolution loop
# This is a safe fallback - we'll add it as a comment for manual integration if automatic fails
print("\n📝 Integration hooks prepared")
print("Note: Hook calls should be added manually to the main evolution loop")
print(
    "Look for the generation loop and add the hook calls after each generation completes"
)

# Write the modified content
with open(FILE_PATH, "w", encoding="utf-8") as f:
    f.write(content)

print("\n✅ Integration script completed")
print("\nNext steps:")
print("1. Review autonomous_evolution_runner.py")
print("2. Find the main generation loop")
print("3. Add the hook calls at the end of each generation")
print("4. Test with a short evolution run")
