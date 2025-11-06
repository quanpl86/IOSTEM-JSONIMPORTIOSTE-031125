# src/map_generator/placements/base_placer.py

# 'abc' là viết tắt của Abstract Base Classes (Lớp cơ sở trừu tượng).
from abc import ABC, abstractmethod
# Sử dụng typing để định nghĩa các kiểu dữ liệu một cách rõ ràng.
from typing import List, Tuple, Dict, Any

# Import lớp PathInfo để sử dụng trong type hinting, đảm bảo tính nhất quán
# về dữ liệu đầu vào cho tất cả các lớp Placer.
from src.map_generator.models.path_info import PathInfo
Coord = Tuple[int, int, int]

class BasePlacer(ABC):
    """
    Lớp cơ sở trừu tượng (Interface) cho tất cả các chiến lược đặt vật phẩm và logic game.
    
    Mỗi lớp con kế thừa từ BasePlacer BẮT BUỘC phải hiện thực hóa
    phương thức place_items(). Nếu không, Python sẽ báo lỗi khi
    khởi tạo đối tượng của lớp con đó.
    """

    @abstractmethod
    def place_items(self, path_info, params: dict) -> dict:
        pass
    def _get_coords(self, path_info: PathInfo) -> List[Coord]:
        """
        [NEW] Lấy danh sách tọa độ phù hợp để đặt vật phẩm.
        Ưu tiên sử dụng `placement_coords` nếu có, nếu không thì dùng `path_coords`.
        Đây là một phương thức helper chung cho tất cả các placer.
        """
        if path_info.placement_coords:
            # print("    LOG: (Placer) Sử dụng placement_coords.")
            return path_info.placement_coords
        else:
            # print("    LOG: (Placer) Sử dụng path_coords.")
            return path_info.path_coords

    def _exclude_ends(self, coords: List[Coord], path_info: PathInfo) -> List[Coord]:
        """
        [NEW] Loại bỏ các tọa độ bắt đầu và kết thúc khỏi danh sách.
        Đây là một thao tác phổ biến để tránh đặt vật phẩm/chướng ngại vật
        ngay tại điểm xuất phát hoặc đích đến của người chơi.
        """
        return [c for c in coords if c != path_info.start_pos and c != path_info.target_pos]

    def _base_layout(self, path_info: PathInfo, items: List[Dict], obstacles: List[Dict]) -> Dict[str, Any]:
        """
        Helper method to construct the final layout dictionary.
        """
        return {
            "start_pos": path_info.start_pos,
            "target_pos": path_info.target_pos,
            "items": items,
            "obstacles": obstacles
        }