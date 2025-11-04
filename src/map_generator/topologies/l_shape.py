# src/map_generator/topologies/l_shape.py
import random
from .base_topology import BaseTopology
from src.map_generator.models.path_info import PathInfo, Coord
from src.utils.geometry import add_vectors, FORWARD_X, FORWARD_Z, BACKWARD_X, BACKWARD_Z

class LShapeTopology(BaseTopology):
    """
    Tạo đường đi hình chữ L.
    Hỗ trợ turn_direction: "right" / "left"
    """

    def generate_path_info(self, grid_size: tuple, params: dict) -> PathInfo:
        print("    LOG: Generating 'l_shape' topology...")

        # === 1. ĐỌC THAM SỐ ===
        leg1_len = params.get('leg1_length', random.randint(3, 5))
        leg2_len = params.get('leg2_length', random.randint(3, 5))
        turn_dir = params.get('turn_direction', 'right').lower()  # "right" hoặc "left"

        # === 2. ĐẢM BẢO TRONG MAP ===
        max_dim = min(grid_size[0], grid_size[2]) - 2
        leg1_len = max(2, min(leg1_len, max_dim - 1))
        leg2_len = max(2, min(leg2_len, max_dim - 1))

        # === 3. CHỌN ĐIỂM BẮT ĐẦU ===
        start_x = random.randint(1, grid_size[0] - leg1_len - 2)
        start_z = random.randint(1, grid_size[2] - leg2_len - 2)
        start_pos: Coord = (start_x, 0, start_z)

        # === 4. CHỌN HƯỚNG ĐẦU NGẪU NHIÊN ===
        initial_dir = random.choice([FORWARD_X, BACKWARD_X, FORWARD_Z, BACKWARD_Z])

        # === 5. TÍNH HƯỚNG RẼ ===
        TURN_MAP = {
            FORWARD_X:  {"right": FORWARD_Z,  "left": BACKWARD_Z},
            BACKWARD_X: {"right": BACKWARD_Z, "left": FORWARD_Z},
            FORWARD_Z:  {"right": BACKWARD_X, "left": FORWARD_X},
            BACKWARD_Z: {"right": FORWARD_X,  "left": BACKWARD_X}
        }
        dir1 = initial_dir
        dir2 = TURN_MAP[dir1][turn_dir]

        # === 6. VẼ ĐƯỜNG ĐI ===
        path_coords: List[Coord] = [start_pos]
        current_pos = start_pos

        # Cạnh 1
        for _ in range(leg1_len):
            current_pos = add_vectors(current_pos, dir1)
            path_coords.append(current_pos)

        # Cạnh 2
        for _ in range(leg2_len):
            current_pos = add_vectors(current_pos, dir2)
            path_coords.append(current_pos)

        target_pos = path_coords[-1]

        return PathInfo(
            start_pos=start_pos,
            target_pos=target_pos,
            path_coords=path_coords,
            placement_coords=path_coords  # BẮT BUỘC GÁN
        )