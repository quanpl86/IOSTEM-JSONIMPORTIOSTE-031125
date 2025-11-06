import random
from typing import Any, Dict, List
from .base_strategy import BaseBugStrategy


def _find_blocks_recursively(program_part: List[Dict], condition: callable) -> List[Dict]:
    """Hàm helper để tìm tất cả các khối thỏa mãn một điều kiện trong cấu trúc chương trình."""
    found_blocks = []
    for block in program_part:
        if condition(block):
            found_blocks.append(block)
        # Đệ quy vào các khối lồng nhau (vòng lặp, if, v.v.)
        if "body" in block and isinstance(block["body"], list):
            found_blocks.extend(_find_blocks_recursively(block["body"], condition))
        if "orelse" in block and isinstance(block["orelse"], list):
            found_blocks.extend(_find_blocks_recursively(block["orelse"], condition))
    return found_blocks


class IncorrectLoopConditionBug(BaseBugStrategy):
    """
    Lỗi Cấu trúc điều khiển: Sai điều kiện vòng lặp.
    Tìm một khối 'controls_whileUntil' và đảo ngược điều kiện của nó.
    Ví dụ: 'while is_path_ahead' -> 'while not is_path_ahead'.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Tìm tất cả các khối vòng lặp while
        while_loops = _find_blocks_recursively(
            program_dict.get("main", []),
            lambda block: block.get("type") == "controls_whileUntil"
        )

        if not while_loops:
            print("   - ⚠️ Không tìm thấy khối 'controls_whileUntil' để tạo lỗi.")
            return program_dict

        target_loop = random.choice(while_loops)
        original_condition = target_loop.get("condition")

        if not original_condition:
            print("   - ⚠️ Khối 'controls_whileUntil' không có điều kiện để tạo lỗi.")
            return program_dict

        # Tạo một khối 'logic_negate' để bọc điều kiện gốc
        negated_condition = {
            "type": "logic_negate",
            "condition": original_condition
        }

        # Thay thế điều kiện cũ bằng điều kiện đã bị đảo ngược
        target_loop["condition"] = negated_condition
        print(f"      -> Bug 'incorrect_loop_condition': Đã đảo ngược điều kiện của một vòng lặp 'while'.")

        return program_dict


class MissingFunctionCallBug(BaseBugStrategy):
    """
    Lỗi Gọi hàm: Thiếu lệnh gọi hàm.
    Xóa một khối gọi hàm ('procedures_callnoreturn') khỏi chương trình chính.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        main_body = program_dict.get("main", [])

        # Tìm tất cả các khối gọi hàm trong chương trình chính
        function_calls = [
            (i, block) for i, block in enumerate(main_body)
            if block.get("type") == "CALL"
        ]

        if not function_calls:
            print("   - ⚠️ Không tìm thấy khối gọi hàm nào trong 'main' để xóa.")
            return program_dict

        # Chọn một khối gọi hàm ngẫu nhiên để xóa
        index_to_remove, block_removed = random.choice(function_calls)
        removed_block = main_body.pop(index_to_remove)
        print(f"      -> Bug 'missing_function_call': Đã xóa lệnh gọi hàm '{removed_block.get('name')}' ở vị trí {index_to_remove}.")

        return program_dict