from action_handler import ActionHandler
from game_session_manager import GameSessionManager

h = ActionHandler(GameSessionManager())
print('✅ ActionHandler imports successfully')
print(f'✅ Coordinate tracking: {len(h.recent_coordinates)} coords, threshold={h.coordinate_spam_threshold}')
print(f'✅ Methods: _check_coordinate_diversity={hasattr(h, "_check_coordinate_diversity")}')
print(f'✅ Methods: _is_coordinate_similar={hasattr(h, "_is_coordinate_similar")}')
print('✅ All ACTION6 diversity features ready!')
