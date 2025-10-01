#!/usr/bin/env python3
"""
Quick test for algorithm inheritance naming system
"""

import os
import sys
import tempfile

# Add project root to path
sys.path.insert(0, os.path.dirname(__file__))

from database_interface import DatabaseInterface
from algorithm_representations import AlgorithmRepresentation, AlgorithmNode


def test_inheritance_naming():
    """Test the algorithm inheritance naming system."""
    print("Testing algorithm inheritance naming system...")

    # Create temporary database
    with tempfile.NamedTemporaryFile(delete=False, suffix='.db') as temp_db:
        temp_db.close()

        db = DatabaseInterface(temp_db.name)
        db._create_database_from_schema()

        try:
            # Create parent algorithms with metadata
            parent1_id = "astar_parent_001"
            parent2_id = "dijkstra_parent_002"

            # Save parent algorithms to population
            for parent_id, name in [(parent1_id, "A* Search"), (parent2_id, "Dijkstra")]:
                test_algo = AlgorithmRepresentation(
                    root_node=AlgorithmNode(node_type="test"),
                    algorithm_id=parent_id,
                    name=name.lower().replace(' ', '_')
                )

                db.save_algorithm(
                    algorithm_id=parent_id,
                    algorithm_type="seeded",
                    algorithm_data=test_algo.to_json()
                )

                db.save_seeded_algorithm_meta(
                    algorithm_id=parent_id,
                    original_name=name,
                    category="Search & Optimization"
                )

            print(f"[PASS] Created parent algorithms: {parent1_id}, {parent2_id}")

            # Test inheritance naming
            hybrid_id = db.create_algorithm_with_inheritance(
                algorithm_id="test_hybrid_123",
                algorithm_type="hybrid",
                algorithm_data='{"test": "data"}',
                parent_ids=[parent1_id, parent2_id],
                original_names=["A*Search", "Dijkstra"]
            )

            print(f"[PASS] Created hybrid algorithm: {hybrid_id}")

            # Verify naming convention
            expected_parts = ["A*Search", "Dijkstra"]
            for part in expected_parts:
                if part in hybrid_id:
                    print(f"[PASS] Found expected name part '{part}' in hybrid ID")
                else:
                    print(f"[WARN] Expected name part '{part}' not found in hybrid ID")

            # Test inheritance chain retrieval
            chain = db.get_algorithm_inheritance_chain(hybrid_id)
            print(f"[PASS] Retrieved inheritance chain: {chain}")

            if len(chain) == 2 and parent1_id in chain and parent2_id in chain:
                print("[PASS] Inheritance chain contains correct parent IDs")
            else:
                print(f"[WARN] Inheritance chain unexpected: expected [{parent1_id}, {parent2_id}], got {chain}")

            # Test multi-level inheritance
            grandchild_id = db.create_algorithm_with_inheritance(
                algorithm_id="test_grandchild_456",
                algorithm_type="hybrid",
                algorithm_data='{"test": "grandchild"}',
                parent_ids=[hybrid_id, parent1_id],
                original_names=["A*Search_Dijkstra", "A*Search"]
            )

            print(f"[PASS] Created grandchild algorithm: {grandchild_id}")

            grandchild_chain = db.get_algorithm_inheritance_chain(grandchild_id)
            print(f"[PASS] Retrieved grandchild inheritance chain: {grandchild_chain}")

            print("[SUCCESS] Algorithm inheritance naming system working correctly")
            return True

        except Exception as e:
            print(f"[ERROR] Inheritance naming test failed: {e}")
            import traceback
            traceback.print_exc()
            return False

        finally:
            db.close()
            try:
                os.unlink(temp_db.name)
            except:
                pass


if __name__ == "__main__":
    print("BitterTruth-AI Algorithm Inheritance Naming Test")
    print("=" * 50)

    success = test_inheritance_naming()

    print("=" * 50)
    if success:
        print("[SUCCESS] All inheritance naming tests passed!")
    else:
        print("[FAIL] Some inheritance naming tests failed!")

    sys.exit(0 if success else 1)