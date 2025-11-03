# src/map_generator/placements/spiral_3d_placer.py

import json
import random
from .base_placer import BasePlacer
from src.map_generator.models.path_info import PathInfo

class Spiral3DPlacer(BasePlacer):
    """
    Đặt vật phẩm cho map xoắn ốc 3D.
    """
    def place_items(self, path_info: PathInfo, params: dict) -> dict:
        print("    LOG: Placing items with 'spiral_3d' logic...")

        # [CẢI TIẾN] Chuyển sang chuẩn 'items_to_place' để đồng nhất hệ thống.
        # Mặc định là 4 crystal để tương thích với các map cũ.
        items_to_place_param = params.get('items_to_place', ['crystal'] * 4)
        
        # [SỬA LỖI] Xử lý trường hợp `items_to_place` được truyền dưới dạng chuỗi JSON.
        items_to_place = []
        if isinstance(items_to_place_param, str):
            try: # Cố gắng parse chuỗi JSON
                items_to_place = json.loads(items_to_place_param.replace("'", '"'))
            except json.JSONDecodeError: # Nếu thất bại, coi nó là một item đơn lẻ
                items_to_place = [items_to_place_param]
        elif isinstance(items_to_place_param, list):
            items_to_place = items_to_place_param

        items = []
        if items_to_place:
            # Lấy các vị trí có thể đặt, loại bỏ điểm đầu và cuối.
            possible_coords = [p for p in path_info.path_coords if p != path_info.start_pos and p != path_info.target_pos]
            
            # [CẢI TIẾN] Tính toán bước nhảy (step) để rải đều vật phẩm trên đường đi.
            # Điều này tạo ra một quy luật rõ ràng hơn là đặt ngẫu nhiên.
            num_items = len(items_to_place)
            if num_items > 0 and len(possible_coords) > num_items:
                step = len(possible_coords) // (num_items + 1)
                if step == 0: step = 1
                
                for i, item_type in enumerate(items_to_place):
                    index = (i + 1) * step
                    if index < len(possible_coords):
                        pos = possible_coords[index]
                        items.append({"type": item_type, "pos": pos})

        return {"start_pos": path_info.start_pos, "target_pos": path_info.target_pos, "items": items, "obstacles": path_info.obstacles}