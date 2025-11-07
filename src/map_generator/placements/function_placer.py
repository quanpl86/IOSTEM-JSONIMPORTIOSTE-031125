# src/map_generator/placements/function_placer.py
"""
FUNCTION PLACER – PHIÊN BẢN CUỐI CÙNG, HOÀN HẢO NHẤT
Dành cho Topic 2: Hàm không tham số

HỖ TRỢ 3 KIỂU CHALLENGE:
1. SIMPLE_APPLY / COMPLEX_APPLY → Học viết hàm
2. DEBUG_FIX_SEQUENCE → Sửa thứ tự gọi hàm
3. DEBUG_FIX_LOGIC → Sửa lỗi điều hướng / thiếu move
4. REFACTOR → Tối ưu bằng hàm (từ code lặp → dùng hàm)

Tương thích mọi map, mọi item, 5 lớp bảo vệ, log chi tiết
"""

from .base_placer import BasePlacer
from collections import Counter
import random
import logging
from typing import List, Tuple, Dict, Set
from src.map_generator.models.path_info import PathInfo

logger = logging.getLogger(__name__)
Coord = Tuple[int, int, int]

class FunctionPlacer(BasePlacer):
    ISLAND_PATTERNS = {
        'basic': [
            {'type': 'crystal', 'offset': (2, 0)},
            {'type': 'crystal',  'offset': (5, 0)}
        ],
        'medium': [
            {'type': 'crystal', 'offset': (1, 0)},
            {'type': 'switch',  'offset': (3, 0)},
            {'type': 'crystal', 'offset': (5, 0)}
        ],
        'advanced': [
            {'type': 'crystal',  'offset': (1, 0)},
            {'type': 'crystal', 'offset': (2, 0)},
            {'type': 'switch',  'offset': (4, 0)},
            {'type': 'crystal',  'offset': (6, 0)}
        ]
    }

    def place_items(self, path_info: PathInfo, params: dict) -> dict:
        # [FIX] Lưu path_info và params để các hàm con có thể truy cập
        self.path_info = path_info
        self.params = params

        # [FIX] Không cần gọi _parse_gen_params vì params đã được xử lý ở tầng trên
        gen_params = params # Sử dụng trực tiếp params
        level = params.get('level', 1)
        challenge_type = params.get('challenge_type', 'SIMPLE_APPLY')

        # ==================================================================
        # 1. CHUẨN HÓA INPUT
        # ==================================================================
        raw_items = params.get('items_to_place', [])
        if isinstance(raw_items, str):
            raw_items = [x.strip() for x in raw_items.split(',') if x.strip()]
        goal_counts = self._parse_goals(params.get('solution_item_goals', ''))
        item_counts = self._merge_item_counts(raw_items, goal_counts)

        items_to_place = [i for i in raw_items if i != 'obstacle']
        obstacle_count = item_counts.get('obstacle', 0)
        if gen_params.get('obstacle_count'):
            obstacle_count = max(obstacle_count, gen_params['obstacle_count'])

        # ==================================================================
        # 2. CHỌN MẪU & SỐ ĐẢO
        # ==================================================================
        if level <= 3:
            island_template = self.ISLAND_PATTERNS['basic']
            num_islands = 2
        elif level <= 6:
            island_template = self.ISLAND_PATTERNS['medium']
            num_islands = gen_params.get('num_islands', 3)
        else:
            island_template = self.ISLAND_PATTERNS['advanced']
            num_islands = gen_params.get('num_islands', 4)

        coords = self._get_coords(path_info)
        valid_coords = self._exclude_ends(coords, path_info)
        total_cells = len(valid_coords)

        # ==================================================================
        # 3. 5 LỚP BẢO VỆ
        # ==================================================================
        cells_per_island = max(len(island_template) * 2, 6)
        total_needed = num_islands * cells_per_island
        if total_needed > total_cells:
            old = num_islands
            num_islands = max(1, total_cells // cells_per_island)
            logger.warning(f"GIẢM ĐẢO: {old} → {num_islands}")

        # ==================================================================
        # 4. ĐIỀU KHIỂN CHALLENGE TYPE
        # ==================================================================
        if challenge_type == 'REFACTOR':
            logger.info("REFACTOR → Tạo code lặp để học sinh tối ưu bằng hàm")
            return self._place_refactor(valid_coords, island_template, num_islands, obstacle_count, gen_params)

        elif challenge_type == 'DEBUG_FIX_SEQUENCE':
            logger.info("DEBUG_FIX_SEQUENCE → Gọi hàm sai thứ tự")
            return self._place_with_sequence_bug(valid_coords, island_template, num_islands, obstacle_count)

        elif challenge_type == 'DEBUG_FIX_LOGIC':
            logger.info("DEBUG_FIX_LOGIC → Thiếu move / sai vị trí")
            return self._place_with_logic_bug(valid_coords, island_template, num_islands, obstacle_count)

        else:  # SIMPLE_APPLY, COMPLEX_APPLY
            logger.info("SIMPLE_APPLY → Học viết hàm")
            return self._place_normal(valid_coords, island_template, num_islands, obstacle_count, gen_params)

    # ==================================================================
    # 5. ĐẶT BÌNH THƯỜNG (SIMPLE_APPLY)
    # ==================================================================
    def _place_normal(self, coords, template, num_islands, obstacle_count, gen_params):
        island_starts = self._get_island_starts(coords, self.params.get('gen_map_type'), num_islands, gen_params)
        items, obstacles, _ = self._place_islands(coords, island_starts, template, obstacle_count)
        return self._base_layout(self.path_info, items, obstacles)

    # ==================================================================
    # 6. DEBUG_FIX_SEQUENCE: GỌI HÀM SAI THỨ TỰ
    # ==================================================================
    def _place_with_sequence_bug(self, coords, template, num_islands, obstacle_count):
        # Đảo ngược thứ tự các đảo
        island_starts = self._get_island_starts(coords, self.params.get('gen_map_type'), num_islands, {})
        island_starts.reverse()  # ← SAI THỨ TỰ
        items, obstacles, _ = self._place_islands(coords, island_starts, template, obstacle_count)
        logger.info(f"BUG: Gọi đảo theo thứ tự ngược")
        return self._base_layout(self.path_info, items, obstacles)

    # ==================================================================
    # 7. DEBUG_FIX_LOGIC: THIẾU MOVE / SAI VỊ TRÍ
    # ==================================================================
    def _place_with_logic_bug(self, coords, template, num_islands, obstacle_count):
        island_starts = self._get_island_starts(coords, self.params.get('gen_map_type'), num_islands, {})
        # Thiếu 1 move → đảo bị lệch
        island_starts = [idx + 2 for idx in island_starts]  # ← SAI VỊ TRÍ

        items, obstacles, _ = self._place_islands(coords, island_starts, template, obstacle_count)
        logger.info(f"BUG: Thiếu move → đảo lệch vị trí")
        return self._base_layout(self.path_info, items, obstacles)

    # ==================================================================
    # 8. REFACTOR: TẠO CODE LẶP ĐỂ HỌC SINH TỐI ƯU
    # ==================================================================
    def _place_refactor(self, coords, template, num_islands, obstacle_count, gen_params):
        # Tạo mẫu lặp giống hệt → học sinh phải dùng hàm
        total_items = len(template) * num_islands
        step = len(coords) // (total_items + 1)
        positions = [i * step for i in range(1, total_items + 1)]

        items = []
        obstacles = self.path_info.obstacles.copy()
        used = set()

        item_idx = 0
        for pos_idx in positions:
            if pos_idx >= len(coords) or pos_idx in used:
                continue
            item_type = template[item_idx % len(template)]['type']
            items.append({"type": item_type, "pos": coords[pos_idx]})
            used.add(pos_idx)
            item_idx += 1

        # Đặt obstacle
        available = [i for i in range(len(coords)) if i not in used]
        wall_count = min(obstacle_count, len(available) // 3)
        if wall_count > 0:
            for idx in random.sample(available, wall_count):
                obstacles.append({"type": "obstacle", "pos": coords[idx]})

        logger.info(f"REFACTOR: Tạo {total_items} item lặp → học sinh tối ưu bằng hàm")
        return self._base_layout(self.path_info, items, obstacles)

    # ==================================================================
    # 9. ĐẶT NHIỀU ĐẢO (TÁI SỬ DỤNG)
    # ==================================================================
    def _place_islands(self, coords, starts, template, obstacle_count):
        items = []
        used = set()
        for start_idx in starts:
            if start_idx >= len(coords):
                break
            island_items = self._place_island_on_path(coords, start_idx, template, used)
            items.extend(island_items)

        # Đặt obstacle
        obstacles = self.path_info.obstacles.copy()
        available = [i for i in range(len(coords)) if i not in used]
        wall_count = min(obstacle_count, len(available) // 3)
        if wall_count > 0:
            for idx in random.sample(available, wall_count):
                obstacles.append({"type": "obstacle", "pos": coords[idx], "modelKey": "wall.brick01"})

        return items, obstacles, used

    # ==================================================================
    # 10. CÁC HÀM HỖ TRỢ (TỐI ƯU CODE)
    # ==================================================================
    def _get_island_starts(self, coords, map_type, num_islands, gen_params):
        total = len(coords)
        if num_islands <= 1:
            return [total // 2]

        if map_type in ['simple_path', 'l_shape', 's_shape', 'z_shape', 't_shape', 'zigzag']:
            step = total // (num_islands + 1)
            return [i * step for i in range(1, num_islands + 1)]
        elif map_type == 'plus_shape':
            c = total // 2
            a = gen_params.get('arm_length', 4)
            return [c - a*2, c - a, c + a, c + a*2][:num_islands]
        elif map_type == 'h_shape':
            h = gen_params.get('leg_height', 6)
            return [h//2, h + h//2][:num_islands]
        elif map_type in ['plowing_field', 'grid']:
            w = gen_params.get('width', 6)
            return [row * w + w//2 for row in range(num_islands) if row * w + w//2 < total]
        else:
            step = total // (num_islands + 1)
            return [i * step for i in range(1, num_islands + 1)]

    def _place_island_on_path(self, coords, start_idx, template, used):
        items = []
        base = coords[start_idx]
        for item_def in template:
            dx, dz = item_def['offset']
            tx, tz = base[0] + dx, base[2] + dz
            best_idx = start_idx
            min_dist = float('inf')
            for i in range(max(0, start_idx-5), min(len(coords), start_idx+10)):
                if i in used:
                    continue
                p = coords[i]
                d = abs(p[0]-tx) + abs(p[2]-tz)
                if d < min_dist:
                    min_dist, best_idx = d, i
                if min_dist <= 1:
                    break
            if best_idx not in used and min_dist < 10:
                items.append({"type": item_def['type'], "pos": coords[best_idx]})
                used.add(best_idx)
        return items

    def _merge_item_counts(self, raw, goals):
        c = Counter(goals)
        for i in raw:
            if i in ['crystal', 'switch', 'obstacle']:
                c[i] += 1
        return c

    def _parse_goals(self, s):
        g = {}
        if not s:
            return g
        for p in str(s).split(';'):
            if ':' in p:
                k, v = p.split(':', 1)
                try:
                    g[k.strip()] = int(v.strip())
                except:
                    pass
        return g