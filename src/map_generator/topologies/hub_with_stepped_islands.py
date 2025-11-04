# src/map_generator/topologies/hub_with_stepped_islands.py

import random
from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord
from src.utils.geometry import add_vectors, FORWARD_Z, FORWARD_X, BACKWARD_Z, BACKWARD_X, UP_Y, DOWN_Y

class HubWithSteppedIslandsTopology(BaseTopology):
    """
    Tạo ra một hòn đảo trung tâm và 4 hòn đảo vệ tinh ở các độ cao khác nhau,
    được nối với nhau bằng các bậc thang đi lên hoặc đi xuống.
    """

    def _create_square_platform(self, center: Coord, size: int) -> list[Coord]:
        """Tạo một nền tảng hình vuông với tâm tại `center` và kích thước `size`."""
        cx, cy, cz = center
        half = size // 2
        platform_coords = []
        for x_offset in range(-half, half + 1):
            for z_offset in range(-half, half + 1):
                platform_coords.append((cx + x_offset, cy, cz + z_offset))
        return platform_coords

    def _create_staircase(self, start_point: Coord, direction: Coord, num_steps: int) -> tuple[list[Coord], list[Coord], list[Coord]]:
        """
        [CHUẨN HÓA] Tạo cầu thang rỗng (chỉ có bề mặt).
        `num_steps` dương thì đi lên, âm thì đi xuống.
        `direction` là hướng di chuyển trên mặt phẳng (X, Z).
        Returns:
            - path_coords: Đường đi của người chơi.
            - surface_coords: Các khối bề mặt của bậc thang.
            - obstacle_coords: Các khối được coi là vật cản (chính là surface_coords).
        """
        path = []
        surfaces = []
        current_pos = start_point
        vertical_step = UP_Y if num_steps > 0 else DOWN_Y

        for _ in range(abs(num_steps)):
            # Bước 1: Đi ngang theo hướng đã cho
            current_pos = add_vectors(current_pos, direction)
            path.append(current_pos)
            # Bước 2: Đi lên hoặc xuống
            current_pos = add_vectors(current_pos, vertical_step)
            surfaces.append(current_pos)
            path.append(current_pos)

        return path, surfaces, surfaces

    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        print("    LOG: Generating 'hub_with_stepped_islands' topology...")

        hub_size = params.get('hub_size', 3)
        island_size = params.get('island_size', 3)
        # Khoảng cách ngang giữa các đảo (số bậc thang)
        gap_size = params.get('gap_size', 3)
        # Các mức chênh lệch độ cao có thể có cho các đảo
        height_options = params.get('height_options', [-gap_size, -gap_size+1, gap_size-1, gap_size])
        
        # Đặt trung tâm vào giữa bản đồ
        center_x = grid_size[0] // 2
        center_z = grid_size[2] // 2
        
        path_coords = []
        placement_coords = []
        obstacles = []

        # 1. Tạo hòn đảo trung tâm (Hub)
        hub_center: Coord = (center_x, 0, center_z)
        start_pos = hub_center # Người chơi bắt đầu ở giữa Hub
        hub_coords = self._create_square_platform(hub_center, hub_size)
        placement_coords.extend(hub_coords)
        path_coords.append(start_pos)

        # 2. Xác định vị trí và độ cao cho 4 đảo vệ tinh
        directions = [FORWARD_Z, FORWARD_X, BACKWARD_Z, BACKWARD_X] # Bắc, Đông, Nam, Tây
        random.shuffle(height_options) # Xáo trộn độ cao để mỗi lần tạo map khác nhau
        
        # 3. Vòng lặp tạo cầu thang và các đảo
        last_pos_on_hub = start_pos
        for i in range(4):
            direction = directions[i]
            height_diff = height_options[i] # Lấy độ cao đã được xáo trộn

            # Điểm bắt đầu của cầu thang, nằm ở rìa của Hub
            stair_start_point = (
                hub_center[0] + direction[0] * (hub_size // 2),
                hub_center[1],
                hub_center[2] + direction[2] * (hub_size // 2)
            )

            # Tạo đường đi từ vị trí cuối cùng trên Hub ra rìa
            # (Giả định đi thẳng, cần thuật toán phức tạp hơn nếu Hub lớn)
            path_coords.append(stair_start_point)
            
            # Tạo cầu thang
            # Số bậc thang ngang = khoảng cách, số bậc thang dọc = độ cao
            # Để đơn giản, ta cho số bậc thang = chênh lệch độ cao
            stair_path, stair_surfaces, stair_obstacles = self._create_staircase(stair_start_point, direction, height_diff)
            
            obstacles.extend([{"modelKey": "ground.checker", "pos": pos} for pos in stair_obstacles])

            # Điểm cuối của cầu thang cũng là điểm vào của đảo vệ tinh
            island_entry_point = stair_path[-1] if stair_path else stair_start_point

            # Tạo hòn đảo vệ tinh
            # Dịch chuyển tâm đảo ra xa một chút so với điểm vào
            island_center = (
                island_entry_point[0] + direction[0] * (island_size // 2),
                island_entry_point[1],
                island_entry_point[2] + direction[2] * (island_size // 2)
            )
            island_coords = self._create_square_platform(island_center, island_size)
            
            # Cập nhật đường đi và các khối cần đặt
            # Đường đi của solver sẽ bao gồm cả việc đi qua cầu thang
            path_coords.extend(stair_path)
            path_coords.append(island_center) # Đi vào giữa đảo
            # Quay trở lại Hub để đi đến đảo tiếp theo
            path_coords.extend(reversed(stair_path))
            path_coords.append(stair_start_point)
            path_coords.append(hub_center) # Quay về trung tâm hub
            
            # Các vị trí có thể đặt vật phẩm bao gồm các đảo và hub
            # placement_coords đã chứa hub_coords
            placement_coords.extend(island_coords)
        
        # Dọn dẹp và hoàn thiện
        final_path = list(dict.fromkeys(path_coords)) # Xóa trùng lặp, giữ thứ tự
        final_placement = list(set(placement_coords))
        target_pos = final_path[-1]

        return PathInfo(
            start_pos=start_pos,
            target_pos=target_pos,
            path_coords=final_path,
            placement_coords=final_placement,
            obstacles=obstacles
        )