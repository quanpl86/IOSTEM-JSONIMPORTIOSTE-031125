# src/map_generator/placements/spiral_placer.py

import random
from .base_placer import BasePlacer
from src.map_generator.models.path_info import PathInfo

class SpiralPlacer(BasePlacer):
    """
    Đặt các vật phẩm cho map xoắn ốc 2D.
    Placer này được thiết kế để hoạt động với SpiralTopology.
    """

    def place_items(self, path_info: PathInfo, params: dict) -> dict:
        """
        Nhận một con đường xoắn ốc và đặt vật phẩm lên đó.

        Args:
            path_info (PathInfo): Thông tin đường đi từ một lớp Topology.
            params (dict): Các tham số bổ sung.
                - items_to_place (list): Danh sách các loại vật phẩm cần đặt.
                - item_count (int): Số lượng vật phẩm cần đặt (nếu không có 'items_to_place').

        Returns:
            dict: Một dictionary chứa layout map hoàn chỉnh.
        """
        print("    LOG: Placing items with 'spiral_placer' logic...")

        items = []
        # Lấy tất cả các vị trí có thể đặt, trừ điểm bắt đầu và kết thúc
        possible_coords = [p for p in path_info.path_coords if p != path_info.start_pos and p != path_info.target_pos]
        random.shuffle(possible_coords)

        # [CẢI TIẾN] Ưu tiên sử dụng 'items_to_place' nếu có
        items_to_place = params.get('items_to_place')
        if items_to_place and isinstance(items_to_place, list):
            for item_type in items_to_place:
                if not possible_coords:
                    print(f"    ⚠️ Cảnh báo: Không còn vị trí trống để đặt '{item_type}'.")
                    break
                pos = possible_coords.pop(0)
                items.append({"type": item_type, "pos": pos})
        else:
            # Nếu không, quay về logic cũ với item_count
            item_count = params.get('item_count', 5)
            item_type = params.get('item_type', 'crystal')
            selected_coords = random.sample(possible_coords, min(item_count, len(possible_coords)))
            items = [{"type": item_type, "pos": pos} for pos in selected_coords]

        # [FIX] Luôn trả về danh sách obstacles rỗng để không đặt vật cản
        return {"start_pos": path_info.start_pos, "target_pos": path_info.target_pos, "items": items, "obstacles": []}