# src/map_generator/placements/for_loop_placer.py

import random
from .base_placer import BasePlacer
from src.map_generator.models.path_info import PathInfo

class ForLoopPlacer(BasePlacer):
    """
    Đặt các vật phẩm theo một quy luật lặp lại nhất quán.
    
    Placer này được thiết kế để hoạt động với nhiều loại Topology khác nhau
    (StraightLine, Staircase, Square, PlowingField) để tạo ra các thử thách
    về Vòng lặp For. Nó tin tưởng rằng Topology đã cung cấp các tọa độ
    quan trọng trong `path_info.path_coords`.
    """

    def place_items(self, path_info: PathInfo, params: dict) -> dict:
        """
        Nhận một con đường có cấu trúc và đặt một vật phẩm lên mỗi điểm
        quan trọng của con đường đó.

        Args:
            path_info (PathInfo): Thông tin đường đi từ một lớp Topology.
            params (dict): Các tham số bổ sung (không được sử dụng trong placer này).

        Returns:
            dict: Một dictionary chứa layout map hoàn chỉnh.
        """
        print("    LOG: Placing items with 'for_loop' logic...")

        # (CẢI TIẾN) Ưu tiên sử dụng placement_coords nếu có, nếu không thì dùng path_coords
        coords_to_place_on = path_info.placement_coords if path_info.placement_coords else path_info.path_coords

        # [CẢI TIẾN] Đọc loại và số lượng vật phẩm từ params để tăng tính linh hoạt.
        # Nếu không có, quay về hành vi mặc định là đặt 'crystal' ở mọi nơi.
        item_type = params.get('item_type', 'crystal')
        item_count = params.get('item_count')
        
        # Lấy tất cả các vị trí có thể đặt (trừ start và target)
        possible_coords = [pos for pos in coords_to_place_on if pos != path_info.target_pos and pos != path_info.start_pos]
        
        items = []
        if item_count is not None:
            # Nếu có 'item_count', chọn ngẫu nhiên 'item_count' vị trí để đặt.
            selected_coords = random.sample(possible_coords, min(item_count, len(possible_coords)))
            items = [{"type": item_type, "pos": pos} for pos in selected_coords]
        else:
            # Nếu không có 'item_count', giữ nguyên logic cũ: đặt ở tất cả các vị trí.
            # Logic này rất quan trọng cho các map như PlowingField (nested_for_loop)
            # nơi tất cả các ô cần có vật phẩm để tạo ra quy luật.
            items = [{"type": item_type, "pos": pos} for pos in possible_coords]
        
        # Trong các bài toán về vòng lặp for, chúng ta thường không thêm chướng ngại vật
        # để người chơi có thể tập trung hoàn toàn vào việc nhận biết quy luật lặp.
        obstacles = []

        return {
            "start_pos": path_info.start_pos,
            "target_pos": path_info.target_pos,
            "items": items,
            "obstacles": obstacles
        }