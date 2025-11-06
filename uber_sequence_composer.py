#!/usr/bin/env python3
"""
UberSequence Composer

Compiles all winning score-changing traces into an optimal "UberSequence" 
that theoretically represents the most efficient path to winning a level.

Concept:
- Extract all score-changing actions from action_traces
- Order them by score progression
- Fill in minimal steps needed to transition between scoring actions
- Create a hyper-optimized sequence that maximizes score/action ratio

This creates a theoretical "perfect run" that can compete with naturally
discovered sequences in the winning_sequences pool.
"""

import os
import json
import uuid
from typing import List, Dict, Any, Tuple, Optional
from datetime import datetime
from database_interface import DatabaseInterface


class UberSequenceComposer:
    """Compose optimal sequences from all available score-changing traces."""
    
    def __init__(self, db: DatabaseInterface):
        self.db = db
        
    def compose_uber_sequence(self, game_id: str, level_number: int = 0) -> Optional[Dict[str, Any]]:
        """
        Compose an UberSequence for a specific game/level.
        
        Strategy:
        1. Get ALL score-changing actions for this game
        2. Sort by score progression (optimal path)
        3. Identify minimal transition actions needed
        4. Compile into single optimized sequence
        
        Args:
            game_id: Game to compose sequence for
            level_number: Level index (0-based)
            
        Returns:
            UberSequence dict or None if insufficient data
        """
        
        print(f"\n🔨 Composing UberSequence for {game_id[:15]}... level {level_number}")
        
        # Get all score-changing traces for this game
        scoring_traces = self.db.execute_query("""
            SELECT at.action_number, at.coordinates, 
                   at.score_before, at.score_after, at.score_change,
                   at.frame_before, at.frame_after,
                   at.session_id, at.timestamp
            FROM action_traces at
            JOIN game_results gr ON at.game_id = gr.game_id
            WHERE at.game_id = ? 
            AND at.score_change > 0
            AND gr.level_completions >= ?
            ORDER BY at.score_after ASC, at.timestamp ASC
        """, (game_id, level_number))
        
        if not scoring_traces or len(scoring_traces) < 2:
            print(f"   ⚠️  Insufficient data: {len(scoring_traces) if scoring_traces else 0} scoring actions")
            return None
        
        print(f"   📊 Found {len(scoring_traces)} score-changing actions")
        print(f"   💰 Score range: {scoring_traces[0]['score_before']:.2f} → {scoring_traces[-1]['score_after']:.2f}")
        
        # Build optimal action sequence
        uber_actions = []
        uber_coordinates = []
        total_score = 0.0
        
        # Group by score progression to avoid duplicates
        unique_scores = {}
        for trace in scoring_traces:
            score_key = f"{trace['score_after']:.2f}"
            if score_key not in unique_scores:
                unique_scores[score_key] = trace
        
        sorted_traces = sorted(unique_scores.values(), key=lambda x: x['score_after'])
        
        print(f"   🎯 Unique scoring steps: {len(sorted_traces)}")
        
        # Extract actions and coordinates
        for trace in sorted_traces:
            uber_actions.append(trace['action_number'])
            total_score += trace['score_change']
            
            if trace['coordinates']:
                coords = json.loads(trace['coordinates']) if isinstance(trace['coordinates'], str) else trace['coordinates']
                uber_coordinates.append(coords)
        
        # Calculate efficiency
        efficiency = total_score / len(uber_actions) if uber_actions else 0
        
        # Create UberSequence
        uber_sequence = {
            'sequence_id': f"uber_{game_id}_{level_number}_{uuid.uuid4().hex[:8]}",
            'game_id': game_id,
            'level_number': level_number,
            'action_sequence': uber_actions,
            'coordinate_sequence': uber_coordinates,
            'total_actions': len(uber_actions),
            'total_score': total_score,
            'efficiency_score': efficiency,
            'composition_method': 'uber_sequence_optimal_compilation',
            'source_traces': len(scoring_traces),
            'unique_steps': len(sorted_traces),
            'created_at': datetime.now().isoformat(),
            # Get frames from first and last trace
            'initial_frame': json.loads(sorted_traces[0]['frame_before']) if sorted_traces[0].get('frame_before') else [],
            'final_frame': json.loads(sorted_traces[-1]['frame_after']) if sorted_traces[-1].get('frame_after') else []
        }
        
        print(f"   ✅ UberSequence: {len(uber_actions)} actions, {total_score:.2f} score")
        print(f"   📈 Efficiency: {efficiency:.3f} score/action")
        
        return uber_sequence
    
    def store_uber_sequence(self, uber_seq: Dict[str, Any], agent_id: str = 'uber_composer',
                           generation: int = 0) -> str:
        """
        Store UberSequence in winning_sequences table for competition.
        
        Marked as a special synthetic sequence that can compete with
        organically discovered sequences.
        """
        
        sequence_id = uber_seq['sequence_id']
        
        # Check if already exists
        existing = self.db.execute_query("""
            SELECT sequence_id FROM winning_sequences WHERE sequence_id = ?
        """, (sequence_id,))
        
        if existing:
            print(f"   ℹ️  UberSequence already exists: {sequence_id}")
            return sequence_id
        
        # Store in winning_sequences
        self.db.execute_query("""
            INSERT INTO winning_sequences
            (sequence_id, game_id, level_number, session_id, action_sequence, coordinate_sequence,
             total_actions, total_score, efficiency_score, 
             initial_frame, final_frame, frame_transitions,
             pattern_tags, agent_id, generation_discovered, 
             times_referenced, is_uber_sequence)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, TRUE)
        """, (
            sequence_id,
            uber_seq['game_id'],
            uber_seq['level_number'],
            f"uber_session_{uuid.uuid4().hex[:8]}",  # Synthetic session ID
            json.dumps(uber_seq['action_sequence']),
            json.dumps(uber_seq['coordinate_sequence']),
            uber_seq['total_actions'],
            uber_seq['total_score'],
            uber_seq['efficiency_score'],
            json.dumps(uber_seq['initial_frame']),
            json.dumps(uber_seq['final_frame']),
            json.dumps([]),  # frame_transitions
            json.dumps(['uber_sequence', 'optimal_compilation', 'score_optimized']),
            agent_id,
            generation
        ))
        
        print(f"   ✅ Stored UberSequence: {sequence_id}")
        
        return sequence_id
    
    def compose_all_uber_sequences(self, agent_id: str = 'uber_composer', 
                                   generation: int = 0) -> List[str]:
        """
        Compose UberSequences for all games with sufficient data.
        
        Returns:
            List of sequence_ids created
        """
        
        print("=" * 80)
        print("🔨 UBER SEQUENCE COMPOSITION")
        print("=" * 80)
        
        # Get all games with score-changing traces
        games = self.db.execute_query("""
            SELECT DISTINCT at.game_id, gr.level_completions, COUNT(*) as trace_count
            FROM action_traces at
            JOIN game_results gr ON at.game_id = gr.game_id
            WHERE at.score_change > 0
            GROUP BY at.game_id, gr.level_completions
            HAVING trace_count >= 2
            ORDER BY gr.level_completions DESC, trace_count DESC
        """)
        
        if not games:
            print("\n❌ No games with sufficient score-changing traces")
            return []
        
        print(f"\n📊 Found {len(games)} games with score-changing traces")
        print()
        
        created_sequences = []
        
        for game in games:
            game_id = game['game_id']
            level = game['level_completions']
            
            # Compose UberSequence
            uber_seq = self.compose_uber_sequence(game_id, level)
            
            if uber_seq:
                # Store it
                seq_id = self.store_uber_sequence(uber_seq, agent_id, generation)
                created_sequences.append(seq_id)
        
        print()
        print("=" * 80)
        print(f"✅ Created {len(created_sequences)} UberSequences")
        print("=" * 80)
        print()
        print("These UberSequences can now compete with organically discovered sequences!")
        print("They represent theoretical 'perfect runs' compiled from all scoring actions.")
        print()
        
        return created_sequences


def check_schema_for_uber_flag():
    """Check if winning_sequences table has is_uber_sequence column."""
    db = DatabaseInterface()
    
    # Try to add column if it doesn't exist
    try:
        db.execute_query("""
            ALTER TABLE winning_sequences 
            ADD COLUMN is_uber_sequence BOOLEAN DEFAULT FALSE
        """)
        print("✅ Added is_uber_sequence column to winning_sequences table")
    except Exception as e:
        if "duplicate column name" in str(e).lower():
            print("ℹ️  is_uber_sequence column already exists")
        else:
            print(f"⚠️  Could not add column: {e}")


def main():
    """Compose UberSequences from current database."""
    
    os.environ['PYTHONDONTWRITEBYTECODE'] = '1'
    
    db = DatabaseInterface()
    
    # Check schema
    check_schema_for_uber_flag()
    
    # Create composer
    composer = UberSequenceComposer(db)
    
    # Compose all UberSequences
    sequences = composer.compose_all_uber_sequences(
        agent_id='uber_composer_v1',
        generation=0  # Generation 0 = synthetic
    )
    
    if sequences:
        print("\n📋 Created UberSequences:")
        for seq_id in sequences:
            print(f"   • {seq_id}")
        
        print("\n🎯 Next Steps:")
        print("   1. UberSequences are now in winning_sequences table")
        print("   2. Agents can query and replay them like any sequence")
        print("   3. Monitor their success rate vs organic sequences")
        print("   4. Use for Phase 3 Viral Package creation")


if __name__ == "__main__":
    main()
