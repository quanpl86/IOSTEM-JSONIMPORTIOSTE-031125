# src/map_generator/topologies/stepped_island_clusters.py

import random
from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord
from src.utils.geometry import add_vectors, FORWARD_X, UP_Y, FORWARD_Z

class SteppedIslandClustersTopology(BaseTopology):
    """
    Tạo ra nhiều cụm đảo, với mỗi cụm ở một độ cao khác nhau,
    được nối với nhau bằng các bậc thang.
    """

    def _create_island(self, top_left_corner: Coord, size: int = 2) -> list[Coord]:
        """Tạo một hòn đảo hình vuông."""
        x, y, z = top_left_corner
        coords = []
        for i in range(size):
            for j in range(size):
                coords.append((x + i, y, z + j))
        return coords

    def _create_staircase(self, start_point: Coord, direction: Coord, num_steps: int) -> tuple[list[Coord], list[Coord], list[Coord]]:
        """
        [CHUẨN HÓA] Tạo cầu thang rỗng, đi lên theo hướng cho trước.
        Returns:
            - path_coords: Đường đi của người chơi.
            - surface_coords: Các khối bề mặt của bậc thang.
            - obstacle_coords: Các khối được coi là vật cản (chính là surface_coords).
        """
        path = []
        surfaces = []
        current_pos = start_point
        for _ in range(num_steps):
            # Bước 1: Đi ngang
            current_pos = add_vectors(current_pos, direction)
            path.append(current_pos)
            # Bước 2: Đi lên
            current_pos = add_vectors(current_pos, UP_Y)
            path.append(current_pos)
            surfaces.append(current_pos) # Chỉ bề mặt trên cùng là khối vật lý
        return path, surfaces, surfaces

    def _create_bridge(self, start_point: Coord, end_point: Coord) -> list[Coord]:
        """Tạo một cây cầu phẳng từ start đến end theo trục X."""
        path = []
        curr_x, y, z = start_point
        end_x = end_point[0]
        step = 1 if end_x > curr_x else -1
        # Bỏ qua điểm đầu tiên vì nó đã tồn tại
        while curr_x != end_x:
            curr_x += step
            path.append((curr_x, y, z))
        return path

    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        """Sinh ra các cụm đảo ở các độ cao khác nhau."""
        print("    LOG: Generating 'stepped_island_clusters' topology...")

        num_clusters = params.get('num_clusters', 2)
        islands_per_cluster = params.get('islands_per_cluster', 2)
        cluster_spacing = params.get('cluster_spacing', 8)
        height_step = params.get('height_step', 2)

        start_x = 2
        start_z = grid_size[2] // 2 - (islands_per_cluster * 2) # Căn giữa cụm đảo
        y = 0

        path_coords: list[Coord] = []
        placement_coords: list[Coord] = []
        obstacles = []

        # Tạo đảo đầu tiên làm điểm bắt đầu
        first_island = self._create_island((start_x, y, start_z), size=2)
        placement_coords.extend(first_island)
        start_pos = (start_x, y, start_z)
        path_coords.append(start_pos)
        last_exit_point = (start_x + 1, y, start_z + 1) # Góc dưới bên phải của đảo đầu tiên
        path_coords.append(last_exit_point)

        for i in range(num_clusters):
            # Tính toán độ cao cho cụm đảo hiện tại
            island_base_y = y + i * height_step
            
            # Nối các đảo trong cụm
            for j in range(islands_per_cluster):
                # Điểm vào của đảo tiếp theo
                next_island_entry = (last_exit_point[0] + 3, island_base_y, last_exit_point[2])
                
                # Tạo cầu nối
                bridge = self._create_bridge(last_exit_point, next_island_entry)
                path_coords.extend(bridge)
                placement_coords.extend(bridge)
                
                # Tạo đảo
                island = self._create_island(next_island_entry, size=2)
                path_coords.append(next_island_entry)
                placement_coords.extend(island)
                
                # Cập nhật điểm ra cho đảo/cầu tiếp theo
                last_exit_point = (next_island_entry[0] + 1, island_base_y, next_island_entry[2] + 1)
                path_coords.append(last_exit_point)

            # Nếu chưa phải cụm cuối, tạo cầu thang đi lên
            if i < num_clusters - 1:
                # [CHUẨN HÓA] Tạo cầu thang và xử lý kết quả
                stair_path, stair_surfaces, stair_obstacles = self._create_staircase(last_exit_point, FORWARD_X, height_step)
                
                path_coords.extend(stair_path)
                # Bề mặt bậc thang cũng là nơi có thể đặt nền móng, nhưng không đặt vật phẩm
                placement_coords.extend(stair_surfaces)
                # Các khối bề mặt được coi là vật cản
                obstacles.extend([{"modelKey": "ground.checker", "pos": pos} for pos in stair_obstacles])
                
                # Cập nhật điểm ra là điểm cuối của cầu thang
                last_exit_point = stair_path[-1] if stair_path else last_exit_point

        target_pos = last_exit_point

        return PathInfo(
            start_pos=start_pos,
            target_pos=target_pos,
            path_coords=list(dict.fromkeys(path_coords)),
            placement_coords=list(set(placement_coords)),
            obstacles=obstacles
        )