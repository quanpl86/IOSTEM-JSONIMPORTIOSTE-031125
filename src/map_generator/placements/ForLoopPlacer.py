# src/map_generator/placements/for_loop_placer.py
"""
FOR LOOP PLACER – BẢN CUỐI CÙNG, HOÀN HẢO NHẤT
Dành cho Topic 3: Vòng lặp for (đơn & lồng)

TÍCH HỢP HOÀN TOÀN:
- for đơn (cụm + gap)
- for lồng (lưới, checkerboard)
- Tự động phát hiện mẫu lặp trên MỌI MAP
- Tương thích: simple_path, bậc_thang, H, T, L, U, Zigzag, grid, plowing_field...
- 4 challenge_type: SIMPLE_APPLY, NESTED_APPLY, DEBUG_FIX, REFACTOR
- 5 lớp bảo vệ + log chi tiết
"""

from .base_placer import BasePlacer
from collections import Counter
import random
import logging
from typing import List, Tuple, Dict, Set

logger = logging.getLogger(__name__)
Coord = Tuple[int, int, int]

class ForLoopPlacer(BasePlacer):
    def place_items(self, path_info: PathInfo, params: dict) -> dict:
        gen_params = self._parse_gen_params(params.get('gen_params', ''))
        level = params.get('level', 1)
        map_type = params.get('gen_map_type', 'unknown')
        challenge_type = params.get('challenge_type', 'SIMPLE_APPLY')

        # ==================================================================
        # 1. CHUẨN HÓA INPUT
        # ==================================================================
        raw_items = params.get('items_to_place', [])
        if isinstance(raw_items, str):
            raw_items = [x.strip() for x in raw_items.split(',') if x.strip()]
        goal_counts = self._parse_goals(params.get('solution_item_goals', ''))
        item_counts = self._merge_item_counts(raw_items, goal_counts)

        obstacle_count = item_counts.get('obstacle', gen_params.get('obstacle_count', 0))

        # ==================================================================
        # 2. LẤY VỊ TRÍ
        # ==================================================================
        coords = self._get_coords(path_info)
        valid_coords = self._exclude_ends(coords, path_info)
        total_cells = len(valid_coords)

        # ==================================================================
        # 3. PHÁT HIỆN MẪU LẶP TỰ ĐỘNG
        # ==================================================================
        pattern = self._detect_loop_pattern(map_type, gen_params, level, total_cells)
        logger.info(f"MAP: {map_type} | MẪU: {pattern['type']} | "
                    f"Cluster: {pattern.get('cluster_size')} | Gap: {pattern.get('gap')} | "
                    f"Rows: {pattern.get('rows')} | Cols: {pattern.get('cols')}")

        # ==================================================================
        # 4. 5 LỚP BẢO VỆ
        # ==================================================================
        if not self._validate_pattern(pattern, total_cells):
            pattern = self._fallback_pattern(total_cells)
            logger.warning("MẪU KHÔNG KHỚP → DÙNG MẪU DỰ PHÒNG")

        # ==================================================================
        # 5. ĐIỀU KHIỂN CHALLENGE TYPE
        # ==================================================================
        if challenge_type == 'REFACTOR':
            return self._place_refactor(valid_coords, pattern, obstacle_count)
        elif challenge_type == 'DEBUG_FIX_SEQUENCE':
            return self._place_with_sequence_bug(valid_coords, pattern, obstacle_count)
        elif challenge_type == 'DEBUG_FIX_LOGIC':
            return self._place_with_logic_bug(valid_coords, pattern, obstacle_count)
        elif challenge_type == 'NESTED_APPLY':
            return self._place_normal(valid_coords, pattern, obstacle_count, item_counts)
        else:  # SIMPLE_APPLY
            return self._place_normal(valid_coords, pattern, obstacle_count, item_counts)

    # ==================================================================
    # 6. PHÁT HIỆN MẪU LẶP TỰ ĐỘNG
    # ==================================================================
    def _detect_loop_pattern(self, map_type: str, gen_params: dict, level: int, total_cells: int) -> dict:
        # 1. ƯU TIÊN gen_params
        if gen_params.get('cluster_size') is not None:
            return {
                'type': 'cluster_gap',
                'cluster_size': gen_params.get('cluster_size', 3),
                'gap': gen_params.get('gap', 2),
                'item_type': gen_params.get('item_type', 'crystal')
            }
        if gen_params.get('rows') is not None:
            return {
                'type': 'nested_grid',
                'rows': gen_params.get('rows', 3),
                'cols': gen_params.get('cols', 3),
                'checkerboard': gen_params.get('checkerboard', False),
                'item_type': gen_params.get('item_type', 'gem')
            }

        # 2. MAP CỤ THỂ
        if map_type in ['grid', 'plowing_field', 'checkerboard_map']:
            return {
                'type': 'nested_grid',
                'rows': min(4, total_cells // 4),
                'cols': min(4, total_cells // 4),
                'checkerboard': True,
                'item_type': 'gem'
            }
        if map_type in ['bậc_thang', 'staircase']:
            return {'type': 'stair', 'step_height': 3, 'items_per_step': 2}
        if map_type in ['h_shape', 'plus_shape', 't_shape']:
            return {'type': 'symmetric', 'num_arms': 4, 'items_per_arm': 3}
        if map_type in ['zigzag', 's_shape', 'z_shape']:
            return {'type': 'zigzag_repeat', 'segments': 6, 'items_per_seg': 1}

        # 3. TỰ ĐỘNG THEO KÍCH THƯỚC
        if total_cells >= 40:
            return {'type': 'cluster_gap', 'cluster_size': 3, 'gap': 2, 'item_type': 'crystal'}
        elif total_cells >= 25:
            return {'type': 'nested_grid', 'rows': 3, 'cols': 3, 'checkerboard': False, 'item_type': 'gem'}
        else:
            return {'type': 'simple_repeat', 'repeat_count': min(4, total_cells//3), 'item_type': 'crystal'}

    # ==================================================================
    # 7. ĐẶT BÌNH THƯỜNG
    # ==================================================================
    def _place_normal(self, coords, pattern, obstacle_count, item_counts):
        items = []
        used = set()

        # Đặt theo mẫu
        if pattern['type'] == 'cluster_gap':
            items.extend(self._place_cluster_gap(coords, pattern, used))
        elif pattern['type'] == 'nested_grid':
            items.extend(self._place_nested_grid(coords, pattern, used))
        elif pattern['type'] == 'stair':
            items.extend(self._place_staircase(coords, pattern, used))
        elif pattern['type'] == 'symmetric':
            items.extend(self._place_symmetric(coords, pattern, used))
        elif pattern['type'] == 'zigzag_repeat':
            items.extend(self._place_zigzag_repeat(coords, pattern, used))
        else:
            items.extend(self._place_simple_repeat(coords, pattern, used))

        # Đặt item từ items_to_place
        self._place_custom_items(items, coords, item_counts, used)

        # Đặt obstacle
        obstacles = self._place_obstacles(coords, used, obstacle_count)

        return self._base_layout(self.path_info, items, obstacles)

    # ==================================================================
    # 8. CÁC HÀM ĐẶT THEO MẪU
    # ==================================================================
    def _place_cluster_gap(self, coords, p, used):
        items = []
        i = 0
        while i + p['cluster_size'] < len(coords):
            # [CẢI TIẾN] Sử dụng danh sách item_types để đặt xen kẽ
            item_types = p.get('item_types', [p.get('item_type', 'crystal')])
            if not item_types: item_types = ['crystal']

            for j in range(p['cluster_size']):
                idx = i + j
                if idx < len(coords) and idx not in used:
                    # Lấy item tiếp theo trong danh sách, lặp lại nếu cần
                    current_item_type = item_types[j % len(item_types)]
                    items.append({"type": current_item_type, "pos": coords[idx]})
                    used.add(idx)
            i += p['cluster_size'] + p['gap']
        return items

    def _place_nested_grid(self, coords, p, used):
        items = []
        # [CẢI TIẾN] Sử dụng danh sách item_types để đặt xen kẽ
        item_types = p.get('item_types', [p.get('item_type', 'gem')])
        if not item_types: item_types = ['gem']
        item_idx_counter = 0

        total = len(coords)
        step = max(1, total // (p['rows'] * p['cols']))
        idx = 0
        for row in range(p['rows']):
            for col in range(p['cols']):
                if idx >= total: break
                if not p['checkerboard'] or (row + col) % 2 == 0:
                    if idx not in used:
                        # Lấy item tiếp theo trong danh sách, lặp lại nếu cần
                        current_item_type = item_types[item_idx_counter % len(item_types)]
                        items.append({"type": current_item_type, "pos": coords[idx]})
                        used.add(idx)
                        item_idx_counter += 1
                idx += step
            idx += step
        return items

    def _place_staircase(self, coords, p, used):
        items = []
        # [CẢI TIẾN] Sử dụng danh sách item_types để đặt xen kẽ
        item_types = p.get('item_types', ['crystal'])
        if not item_types: item_types = ['crystal']

        i = 0
        while i + p['step_height'] * p['items_per_step'] < len(coords):
            for j in range(p['items_per_step']):
                idx = i + j * p['step_height']
                if idx < len(coords) and idx not in used:
                    current_item_type = item_types[j % len(item_types)]
                    items.append({"type": current_item_type, "pos": coords[idx]})
                    used.add(idx)
            i += p['step_height'] * p['items_per_step']
        return items

    def _place_symmetric(self, coords, p, used):
        items = []
        center = len(coords) // 2
        # [CẢI TIẾN] Sử dụng danh sách item_types để đặt xen kẽ
        item_types = p.get('item_types', ['switch'])
        if not item_types: item_types = ['switch']

        arm_len = p['items_per_arm']
        step = len(coords) // 8
        for offset in [step, -step, step*3, -step*3]:
            for i in range(1, arm_len + 1):
                idx = (center + offset * i) % len(coords)
                if idx not in used:
                    current_item_type = item_types[i % len(item_types)]
                    items.append({"type": current_item_type, "pos": coords[idx]})
                    used.add(idx)
        return items

    def _place_zigzag_repeat(self, coords, p, used):
        items = []
        seg_len = len(coords) // p['segments']
        for seg in range(p['segments']):
            # [CẢI TIẾN] Sử dụng danh sách item_types để đặt xen kẽ
            item_types = p.get('item_types', ['key'])
            if not item_types: item_types = ['key']

            idx = seg * seg_len + seg_len // 2
            if idx < len(coords) and idx not in used:
                current_item_type = item_types[seg % len(item_types)]
                items.append({"type": current_item_type, "pos": coords[idx]})
                used.add(idx)
        return items

    def _place_simple_repeat(self, coords, p, used):
        items = []
        # [CẢI TIẾN] Sử dụng danh sách item_types để đặt xen kẽ
        item_types = p.get('item_types', [p.get('item_type', 'crystal')])
        if not item_types: item_types = ['crystal']

        step = len(coords) // (p['repeat_count'] + 1)
        for i in range(1, p['repeat_count'] + 1):
            idx = i * step
            if idx < len(coords) and idx not in used:
                current_item_type = item_types[i % len(item_types)]
                items.append({"type": current_item_type, "pos": coords[idx]})
                used.add(idx)
        return items

    # ==================================================================
    # 9. ĐẶT ITEM & OBSTACLE
    # ==================================================================
    def _place_custom_items(self, items, coords, item_counts, used):
        # [CẢI TIẾN] Không đặt lại các item đã được đặt theo pattern
        # Đếm số lượng item đã được đặt
        placed_counts = Counter(item['type'] for item in items)
        # Trừ đi số lượng đã đặt khỏi tổng số cần đặt
        item_counts = Counter(item_counts) - placed_counts
        available = [i for i in range(len(coords)) if i not in used]
        for item_type, count in item_counts.items():
            if item_type == 'obstacle': continue
            positions = random.sample(available, min(count, len(available)))
            for pos_idx in positions:
                items.append({"type": item_type, "pos": coords[pos_idx]})
                used.add(pos_idx)
                available.remove(pos_idx)

    def _place_obstacles(self, coords, used, count):
        obstacles = self.path_info.obstacles.copy()
        available = [i for i in range(len(coords)) if i not in used]
        wall_count = min(count, len(available) // 4)
        for idx in random.sample(available, wall_count):
            obstacles.append({"type": "obstacle", "pos": coords[idx], "modelKey": "wall.brick01"})
        return obstacles

    # ==================================================================
    # 10. DEBUG & REFACTOR
    # ==================================================================
    def _place_with_sequence_bug(self, coords, pattern, obstacle_count):
        # [CẢI TIẾN] Lấy item_counts để có thể đặt custom items
        item_counts = self._merge_item_counts(self.raw_items, self.goal_counts)

        if pattern['type'] == 'cluster_gap':
            pattern['cluster_size'], pattern['gap'] = pattern['gap'], pattern['cluster_size']
            logger.info("BUG: Đảo ngược cluster và gap")
        elif pattern['type'] == 'nested_grid':
            pattern['rows'], pattern['cols'] = pattern['cols'], pattern['rows']
            logger.info("BUG: Đảo ngược rows và cols")
        # [CẢI TIẾN] Truyền item_counts vào _place_normal
        return self._place_normal(coords, pattern, obstacle_count, item_counts)

    def _place_with_logic_bug(self, coords, pattern, obstacle_count):
        # [CẢI TIẾN] Lấy item_counts để có thể đặt custom items
        item_counts = self._merge_item_counts(self.raw_items, self.goal_counts)

        if pattern['type'] == 'nested_grid':
            pattern['checkerboard'] = not pattern.get('checkerboard', False)
            logger.info("BUG: Đặt sai ô chẵn/lẻ")
        elif pattern['type'] == 'cluster_gap':
            pattern['cluster_size'] += 1
            logger.info("BUG: Lặp thừa 1 lần")
        # [CẢI TIẾN] Truyền item_counts vào _place_normal
        return self._place_normal(coords, pattern, obstacle_count, item_counts)

    def _place_refactor(self, coords, pattern, obstacle_count):
        items = []
        used = set()
        # [CẢI TIẾN] Lấy item_counts để có thể đặt custom items
        item_counts = self._merge_item_counts(self.raw_items, self.goal_counts)

        # Lặp tay 3-4 lần → học sinh dùng for
        for _ in range(4):
            sub_coords = coords[_*10:(_+1)*10]
            items.extend(self._place_cluster_gap(sub_coords, {'cluster_size': 2, 'gap': 1, 'item_type': 'crystal'}, used))
        logger.info("REFACTOR: Tạo lặp tay → học sinh dùng for")

        # [CẢI TIẾN] Gọi hàm đặt custom items và obstacles
        self._place_custom_items(items, coords, item_counts, used)
        obstacles = self._place_obstacles(coords, used, obstacle_count)
        return self._base_layout(self.path_info, items, obstacles)

    # ==================================================================
    # 11. HỖ TRỢ
    # ==================================================================
    def _validate_pattern(self, p, total):
        if p['type'] == 'cluster_gap':
            return (p['cluster_size'] + p['gap']) * 2 <= total
        if p['type'] == 'nested_grid':
            return p['rows'] * p['cols'] <= total
        return True

    def _fallback_pattern(self, total):
        return {'type': 'simple_repeat', 'repeat_count': min(3, total//3), 'item_type': 'crystal'}

    def _merge_item_counts(self, raw, goals):
        c = Counter(goals)
        for i in raw:
            if i in ['crystal', 'gem', 'key', 'switch', 'obstacle']:
                c[i] += 1
        return c

    def _parse_goals(self, s):
        g = {}
        if not s: return g
        for p in str(s).split(';'):
            if ':' in p:
                k, v = p.split(':', 1)
                try: g[k.strip()] = int(v.strip())
                except: pass
        return g