# src/map_generator/placements/command_obstacle_placer.py
"""
COMMAND OBSTACLE PLACER – ĐỒNG BỘ HOÀN HẢO VỚI OBSTACLE_PLACER
- Đặt obstacle ở y+1
- Dùng modelKey
- Dùng placement_coords
- Hỗ trợ obstacle_chance + obstacle_count
- 5 lớp bảo vệ
"""

from .base_placer import BasePlacer
from collections import Counter
from src.map_generator.models.path_info import PathInfo
import random
import logging
from typing import List, Tuple, Dict, Set, Any

logger = logging.getLogger(__name__)
Coord = Tuple[int, int, int]

class CommandObstaclePlacer(BasePlacer):

    OBSTACLE_MODELS = ["wall.brick01"]

    def place_items(self, path_info: PathInfo, params: dict) -> dict:
        challenge_type = params.get('challenge_type', 'SIMPLE_APPLY')
        
        # ==================================================================
        # 1. CHUẨN HÓA INPUT
        # ==================================================================
        raw_items = params.get('items_to_place', [])
        if isinstance(raw_items, str):
            raw_items = [x.strip() for x in raw_items.split(',') if x.strip()]
        elif not isinstance(raw_items, list):
            raw_items = []

        goal_counts = self._parse_goals(params.get('itemGoals', {}))
        item_counts = self._merge_item_counts(raw_items, goal_counts)

        items_to_place = [item for item in raw_items if item != 'obstacle']
        for k, v in goal_counts.items():
            if k != 'obstacle':
                items_to_place.extend([k] * v)

        obstacle_count = item_counts.get('obstacle', 0)
        if params.get('obstacle_count'):
            obstacle_count = max(obstacle_count, params['obstacle_count'])

        # ==================================================================
        # 2. LẤY VỊ TRÍ ĐẶT (ƯU TIÊN placement_coords)
        # ==================================================================
        coords = path_info.placement_coords if path_info.placement_coords else path_info.path_coords
        valid_coords = [c for c in coords if c != path_info.start_pos and c != path_info.target_pos]
        total_cells = len(valid_coords)

        logger.info(f"MAP: {params.get('map_type')} | Ô khả dụng: {total_cells} | Item: {len(items_to_place)} | Obstacle: {obstacle_count}")

        # ==================================================================
        # 3. 5 LỚP BẢO VỆ
        # ==================================================================
        total_needed = len(items_to_place) + obstacle_count
        if total_needed > total_cells:
            logger.warning(f"MAP QUÁ NHỎ → GIẢM TỪ {total_needed} XUỐNG {total_cells}")
            obstacle_count = max(0, total_cells - len(items_to_place))

        # ==================================================================
        # 4. ĐẶT THEO CHALLENGE
        # ==================================================================
        if challenge_type in ['DEBUG_FIX_SEQUENCE', 'DEBUG_FIX_LOGIC']:
            items, obstacles = self._place_with_bug(path_info, valid_coords, items_to_place, obstacle_count, challenge_type)
        elif challenge_type == 'REFACTOR':
            from .for_loop_placer import ForLoopPlacer
            logger.info("REFACTOR → ForLoopPlacer")
            return ForLoopPlacer().place_items(path_info, params)
        else:
            items, obstacles = self._place_normal(path_info, valid_coords, items_to_place, obstacle_count, params)

        logger.info(f"ĐÃ ĐẶT: {len(items)} item | {len(obstacles) - len(path_info.obstacles)} obstacle (y+1)")

        return self._base_layout(path_info, items, obstacles)

    # ==================================================================
    # 5. ĐẶT BÌNH THƯỜNG – ĐÚNG VỚI OBSTACLE_PLACER
    # ==================================================================
    def _place_normal(self, path_info: PathInfo, coords: List[Coord], items_to_place: List[str], obstacle_count: int, params: dict):
        items = []
        obstacles = path_info.obstacles.copy()
        used_indices = set()

        # === ĐẶT OBSTACLE TRƯỚC (ở y+1) ===
        obstacle_chance = params.get('obstacle_chance')
        available_coords = [i for i in range(len(coords)) if i not in used_indices]

        if obstacle_chance is not None:
            # Dùng xác suất
            for i in available_coords:
                if random.random() < obstacle_chance:
                    pos = coords[i]
                    wall_pos = (pos[0], pos[1] + 1, pos[2])  # y+1
                    obstacles.append({"type": "obstacle", "pos": wall_pos})
                    used_indices.add(i)
            available_coords = [i for i in available_coords if i not in used_indices]
        else:
            # Dùng số lượng cố định
            wall_count = min(obstacle_count, len(available_coords))
            wall_indices = random.sample(available_coords, wall_count)
            for i in wall_indices:
                pos = coords[i]
                wall_pos = (pos[0], pos[1] + 1, pos[2])  # y+1
                obstacles.append({"type": "obstacle", "pos": wall_pos})
                used_indices.add(i)
            available_coords = [i for i in available_coords if i not in used_indices]

        # === ĐẶT ITEM SAU ===
        item_count = min(len(items_to_place), len(available_coords))
        item_indices = random.sample(available_coords, item_count) if item_count > 0 else []

        for i, item_type in zip(item_indices, items_to_place[:item_count]):
            pos = coords[i]
            if item_type == "switch":
                items.append({"type": item_type, "pos": pos, "initial_state": "off"})
            else:
                items.append({"type": item_type, "pos": pos})

        return items, obstacles

    # ==================================================================
    # 6. ĐẶT VỚI LỖI (DEBUG_FIX)
    # ==================================================================
    def _place_with_bug(self, path_info: PathInfo, coords, items_to_place, obstacle_count, bug_type):
        items = []
        obstacles = path_info.obstacles.copy()
        used_indices = set()

        # BUG 1: Đặt item đầu tiên ở đầu đường → collect sai
        if bug_type == 'DEBUG_FIX_SEQUENCE' and items_to_place:
            items.append({"type": items_to_place[0], "pos": coords[0]})
            remaining_items = items_to_place[1:]
            place_coords = coords[2:]
        else:
            remaining_items = items_to_place
            place_coords = coords

        # Đặt item còn lại
        step = max(1, len(place_coords) // max(1, len(remaining_items)))
        for i, item_type in enumerate(remaining_items):
            idx = i * step
            if idx < len(place_coords):
                pos = place_coords[idx]
                if item_type == "switch":
                    items.append({"type": item_type, "pos": pos, "initial_state": "off"})
                else:
                    items.append({"type": item_type, "pos": pos})
                used_indices.add(idx)

        # BUG 2: Đặt tường ở y+1 → cần jump
        if bug_type == 'DEBUG_FIX_LOGIC' and obstacle_count > 0:
            wall_idx = len(place_coords) // 3
            if wall_idx < len(place_coords):
                pos = place_coords[wall_idx]
                wall_pos = (pos[0], pos[1] + 1, pos[2])
                obstacles.append({"type": "obstacle", "pos": wall_pos})

        return items, obstacles

    # ==================================================================
    # 7. HỖ TRỢ
    # ==================================================================
    def _merge_item_counts(self, raw_items: List[str], goal_counts: dict) -> Counter:
        counts = Counter(goal_counts)
        for item in raw_items:
            if item in ['crystal', 'gem', 'key', 'switch', 'obstacle']:
                counts[item] += 1
        return counts

    def _parse_goals(self, goals_input) -> dict:
        if isinstance(goals_input, dict):
            return {k: v for k, v in goals_input.items() if isinstance(v, (int, str)) and str(v).lower() != 'all'}
        return {}