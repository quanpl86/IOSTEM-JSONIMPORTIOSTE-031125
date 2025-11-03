# src/map_generator/placements/z_shape_placer.py

import random
from .base_placer import BasePlacer
from src.map_generator.models.path_info import PathInfo

class ZShapePlacer(BasePlacer):
    """
    Đặt các vật phẩm cho map hình chữ Z.
    """

    def place_items(self, path_info: PathInfo, params: dict) -> dict:
        """
        Nhận một con đường chữ Z và đặt vật phẩm lên đó.

        Args:
            path_info (PathInfo): Thông tin đường đi từ ZShapeTopology.
            params (dict): Các tham số bổ sung (ví dụ: item_count).

        Returns:
            dict: Một dictionary chứa layout map hoàn chỉnh.
        """
        print("    LOG: Placing items with 'z_shape' logic...")

        # [SỬA LỖI] Đọc trực tiếp danh sách `items_to_place` thay vì `item_count` và `item_type`.
        # Điều này cho phép đặt nhiều loại và số lượng vật phẩm khác nhau.
        items_to_place_param = params.get('items_to_place', [])
        items_to_place = items_to_place_param if isinstance(items_to_place_param, list) else [items_to_place_param]

        possible_coords = [p for p in path_info.path_coords if p != path_info.start_pos and p != path_info.target_pos]
        random.shuffle(possible_coords)

        items = []
        # Đặt từng vật phẩm trong danh sách yêu cầu vào các vị trí có thể đặt
        for i in range(min(len(items_to_place), len(possible_coords))):
            item_type = items_to_place[i]
            pos = possible_coords[i]
            items.append({"type": item_type, "pos": pos})

        return {"start_pos": path_info.start_pos, "target_pos": path_info.target_pos, "items": items, "obstacles": path_info.obstacles}