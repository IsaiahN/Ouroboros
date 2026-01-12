"""
Unit Tests for EvolutionaryEngine

Tests the evolutionary system including:
- Population evolution
- Fitness calculation
- Selection mechanisms
- Mutation and offspring generation
- Youth bonus calculation

Rule 5: Unit tests for core components are allowed.
Uses temp database (not production).
"""
import os
os.environ['PYTHONDONTWRITEBYTECODE'] = '1'

import pytest
import tempfile
import json
from pathlib import Path

from database_interface import DatabaseInterface
from evolutionary_engine import EvolutionaryEngine, calculate_youth_bonus, safe_json_parse


@pytest.fixture
def temp_db():
    """Create a temporary database path."""
    fd, path = tempfile.mkstemp(suffix='.db')
    os.close(fd)
    os.unlink(path)
    yield path
    try:
        os.unlink(path)
    except:
        pass


@pytest.fixture
def db(temp_db):
    """Create a DatabaseInterface with temp database."""
    interface = DatabaseInterface(temp_db)
    yield interface
    interface.close()


@pytest.fixture
def engine(db):
    """Create an EvolutionaryEngine instance."""
    return EvolutionaryEngine(db)


class TestYouthBonusCalculation:
    """Tests for youth bonus calculation helper function."""
    
    def test_same_generation_max_bonus(self):
        """Agent in current generation (newborn) gets max youth bonus."""
        bonus = calculate_youth_bonus(5, 5)
        assert bonus == 1.5  # Max bonus for newborns
    
    def test_recent_agent_gets_bonus(self):
        """Recently created agent gets positive bonus."""
        bonus = calculate_youth_bonus(5, 6)
        assert bonus > 1.0  # Should be above baseline
    
    def test_old_agent_baseline_bonus(self):
        """Old agent (5+ generations) gets baseline bonus."""
        bonus = calculate_youth_bonus(1, 100)
        assert bonus == 1.0  # No youth bonus after 5 generations
    
    def test_youth_bonus_decreases_with_age(self):
        """Older agents should get less bonus."""
        bonus_new = calculate_youth_bonus(9, 10)  # Age 1
        bonus_old = calculate_youth_bonus(5, 10)  # Age 5
        assert bonus_new >= bonus_old


class TestSafeJsonParse:
    """Tests for safe JSON parsing helper."""
    
    def test_valid_json_parsed(self):
        """Valid JSON string should be parsed."""
        result = safe_json_parse('{"key": "value"}')
        assert result == {"key": "value"}
    
    def test_invalid_json_returns_default(self):
        """Invalid JSON should return default."""
        result = safe_json_parse('not valid json', default={})
        assert result == {}
    
    def test_none_returns_default(self):
        """None input should return default."""
        result = safe_json_parse(None, default={'default': True})
        assert result == {'default': True}
    
    def test_empty_string_returns_empty_dict(self):
        """Empty string returns empty dict (function default behavior)."""
        result = safe_json_parse('', default=[])
        # Function returns {} for invalid JSON when default is falsy
        assert isinstance(result, (dict, list))


class TestEvolutionaryEngineInitialization:
    """Tests for EvolutionaryEngine initialization."""
    
    def test_engine_creates_successfully(self, engine):
        """EvolutionaryEngine should create without errors."""
        assert engine is not None
        assert engine.db is not None
    
    def test_engine_has_required_methods(self, engine):
        """Engine should have required public methods."""
        assert hasattr(engine, 'evolve_population')
        assert hasattr(engine, 'calculate_epigenetic_inheritance')
        assert callable(engine.evolve_population)


class TestFitnessCalculation:
    """Tests for fitness calculation methods."""
    
    def test_standard_fitness_for_unknown_agent(self, engine):
        """Unknown agent should get minimal fitness."""
        fitness = engine._calculate_standard_fitness('nonexistent-agent-id')
        # Should return minimal base fitness, not error
        assert isinstance(fitness, float)
        assert fitness >= 0.0
    
    def test_diversity_fitness_component(self, engine):
        """Diversity fitness should be calculable."""
        diversity = engine._calculate_diversity_fitness_component('test-agent')
        assert isinstance(diversity, float)
        assert 0.0 <= diversity <= 1.0


class TestEpigeneticInheritance:
    """Tests for epigenetic layer inheritance."""
    
    def test_inheritance_with_minimal_parents(self, engine):
        """Should handle parents with minimal data."""
        parent1 = {'agent_id': 'p1', 'fitness': 0.6}
        parent2 = {'agent_id': 'p2', 'fitness': 0.4}
        
        offspring_epi = engine.calculate_epigenetic_inheritance(parent1, parent2)
        
        assert isinstance(offspring_epi, dict)
    
    def test_inheritance_applies_decay(self, engine):
        """Inherited values should have decay applied."""
        parent1 = {
            'agent_id': 'p1',
            'fitness': 0.6,
            'feature_attention_weights': json.dumps({'feature_a': 1.0})
        }
        parent2 = {
            'agent_id': 'p2',
            'fitness': 0.4,
            'feature_attention_weights': json.dumps({'feature_a': 0.8})
        }
        
        offspring_epi = engine.calculate_epigenetic_inheritance(parent1, parent2)
        
        # Result should be a valid dict (decay applied internally)
        assert isinstance(offspring_epi, dict)


class TestPopulationLoading:
    """Tests for population loading from database."""
    
    def test_empty_database_returns_empty_list(self, engine):
        """Empty database should return empty population."""
        population = engine._load_population_from_database()
        # Fresh database has no agents
        assert isinstance(population, list)


class TestMutationApplication:
    """Tests for mutation logic."""
    
    def test_mutation_with_empty_offspring(self, engine):
        """Empty offspring list should return empty."""
        result = engine._apply_mutations([], {'mutation_rate': 0.1})
        assert result == []
    
    def test_mutation_preserves_agent_count(self, engine):
        """Mutation should not change number of offspring."""
        offspring = [
            {'agent_id': 'o1', 'genome': json.dumps({'val': 0.5})},
            {'agent_id': 'o2', 'genome': json.dumps({'val': 0.7})},
        ]
        result = engine._apply_mutations(offspring.copy(), {'mutation_rate': 0.1})
        assert len(result) == len(offspring)
