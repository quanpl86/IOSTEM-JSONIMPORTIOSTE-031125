import random
from typing import Any, Dict, List
from .base_strategy import BaseBugStrategy
from typing import Any, Dict, List, Optional


def _find_blocks_recursively(program_part: List[Dict], condition: callable) -> List[Dict]:
    """Hàm helper để tìm tất cả các khối thỏa mãn một điều kiện trong cấu trúc chương trình."""
    found_blocks = []
    for block in program_part:
        if condition(block):
            found_blocks.append(block)
        if "body" in block and isinstance(block["body"], list):
            found_blocks.extend(_find_blocks_recursively(block["body"], condition))
        if "orelse" in block and isinstance(block["orelse"], list):
            found_blocks.extend(_find_blocks_recursively(block["orelse"], condition))
        # [MỚI] Xử lý các khối có 'value' là một dict (ví dụ: variables_set với value là math_arithmetic)
        if "value" in block and isinstance(block["value"], dict):
            found_blocks.extend(_find_blocks_recursively([block["value"]], condition))
        # [MỚI] Xử lý các khối có 'expression' là một dict (ví dụ: maze_repeat_expression)
        if "expression" in block and isinstance(block["expression"], dict):
            found_blocks.extend(_find_blocks_recursively([block["expression"]], condition))
    return found_blocks

def _get_target_scope_blocks_and_ref(program_dict: Dict[str, Any], config: Dict) -> Optional[List[Dict]]:
    """
    Xác định phạm vi tìm kiếm khối lệnh dựa trên 'target' và 'function_name' trong config.
    Trả về tham chiếu đến danh sách các khối lệnh trong phạm vi đó.
    """
    target_scope = config.get("target", "main") # Mặc định là main
    bug_options = config.get("options", {})
    function_name = bug_options.get("function_name")

    if target_scope == "main":
        return program_dict.get("main")
    elif target_scope == "function_body" and function_name:
        return program_dict.get("procedures", {}).get(function_name)
    return None


class IncorrectLoopConditionBug(BaseBugStrategy):
    """
    Lỗi Cấu trúc điều khiển: Sai điều kiện vòng lặp.
    Tìm một khối 'controls_whileUntil' và đảo ngược điều kiện của nó.
    Ví dụ: 'while is_path_ahead' -> 'while not is_path_ahead'.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Tìm tất cả các khối vòng lặp while
        actual_scope_target = config.get("target", "main") # Default to 'main' if not specified
        if actual_scope_target not in ["main", "function_body"]:
            # If target is not a valid scope (e.g., "loop"), default to "main"
            actual_scope_target = "main"

        scope_config = {"target": actual_scope_target}
        if actual_scope_target == "function_body" and config.get("options", {}).get("function_name"):
            scope_config["options"] = {"function_name": config["options"]["function_name"]}

        target_blocks_list = _get_target_scope_blocks_and_ref(program_dict, scope_config)
        if target_blocks_list is None: return program_dict

        if not while_loops:
            print(f"   - ⚠️ Không tìm thấy khối 'controls_whileUntil' để tạo lỗi trong phạm vi '{actual_scope_target}'.")
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
        print(f"      -> Bug 'incorrect_loop_condition': Đã đảo ngược điều kiện của một vòng lặp 'while' trong phạm vi '{actual_scope_target}'.")

        return program_dict


class MissingFunctionCallBug(BaseBugStrategy):
    """
    Lỗi Gọi hàm: Thiếu lệnh gọi hàm.
    Xóa một khối gọi hàm ('procedures_callnoreturn') khỏi chương trình chính.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        main_body = program_dict.get("main", [])
        bug_options = config.get("options", {})
        target_function_name = bug_options.get("function_name_to_remove") # Tên hàm cần xóa lệnh gọi

        # Tìm tất cả các khối gọi hàm trong chương trình chính
        function_calls = [
            (i, block) for i, block in enumerate(main_body)
            if block.get("type") == "CALL" and (not target_function_name or block.get("name") == target_function_name)
        ]

        if not function_calls:
            print(f"   - ⚠️ Không tìm thấy khối gọi hàm nào trong 'main' (hoặc hàm '{target_function_name}') để xóa.")
            return program_dict

        # Chọn một khối gọi hàm ngẫu nhiên để xóa
        index_to_remove, block_removed = random.choice(function_calls)
        removed_block = main_body.pop(index_to_remove)
        print(f"      -> Bug 'missing_function_call': Đã xóa lệnh gọi hàm '{removed_block.get('name')}' ở vị trí {index_to_remove} trong 'main'.")

        return program_dict