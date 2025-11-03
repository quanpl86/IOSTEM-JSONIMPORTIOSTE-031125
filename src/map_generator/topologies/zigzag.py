# src/map_generator/topologies/zigzag.py

import random
from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord
from src.utils.geometry import add_vectors, FORWARD_X, FORWARD_Z

class ZigzagTopology(BaseTopology):
    """
    Tạo ra một con đường hình ziczac trên mặt phẳng 2D.
    Lý tưởng cho các bài học về vòng lặp với các hành động lặp lại có quy luật.
    """

    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        print("    LOG: Generating 'zigzag' topology...")

        num_segments = params.get('num_segments', random.randint(4, 6))
        segment_len = params.get('segment_length', random.randint(2, 3))

        # [SỬA LỖI] Tính toán kích thước cần thiết một cách chính xác hơn.
        # Số đoạn đi theo trục X là ceil(num_segments / 2)
        # Số đoạn đi theo trục Z là floor(num_segments / 2)
        # Điều này xử lý đúng cho cả trường hợp num_segments chẵn và lẻ.
        total_width = segment_len * ((num_segments + 1) // 2)
        total_depth = segment_len * (num_segments // 2)

        # [SỬA LỖI] Đảm bảo giới hạn của randint luôn hợp lệ.
        # Nếu không gian không đủ, ta sẽ không thể sinh map, nhưng ít nhất chương trình không bị crash.
        # Ta dùng max(1, ...) để đảm bảo giới hạn dưới không bao giờ lớn hơn giới hạn trên.
        max_start_x = max(1, grid_size[0] - total_width - 2)
        max_start_z = max(1, grid_size[2] - total_depth - 2)

        # Chọn vị trí bắt đầu
        start_x = random.randint(1, max_start_x)
        start_z = random.randint(1, max_start_z)
        y = 0
        start_pos: Coord = (start_x, y, start_z)

        path_coords: list[Coord] = [start_pos] # Đường đi nên bao gồm cả điểm bắt đầu
        current_pos = start_pos

        # Hướng ban đầu (luân phiên giữa Z và X)
        directions = [FORWARD_Z, FORWARD_X]

        for i in range(num_segments):
            # Chọn hướng cho đoạn hiện tại
            current_dir = directions[i % 2]
            
            # Vẽ đoạn thẳng
            for _ in range(segment_len):
                current_pos = add_vectors(current_pos, current_dir)
                path_coords.append(current_pos)

        target_pos = path_coords[-1]

        return PathInfo(
            start_pos=start_pos,
            target_pos=target_pos,
            path_coords=path_coords,
            placement_coords=path_coords # Đối với zigzag, đường đi và điểm đặt là một
        )