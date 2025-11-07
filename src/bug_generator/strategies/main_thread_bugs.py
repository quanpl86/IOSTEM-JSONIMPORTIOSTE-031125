# src/bug_generator/strategies/main_thread_bugs.py
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
        # Đệ quy vào các khối lồng nhau (vòng lặp, if, v.v.)
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

class MisplacedBlocksBug(BaseBugStrategy):
    """
    1.1. Lỗi Tuần Tự: Sai Thứ Tự Khối Lệnh (Sequence Error)
    Hoán đổi vị trí của hai khối lệnh ngẫu nhiên trong chương trình chính.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Determine the actual scope to search within
        actual_scope_target = config.get("target", "main") # Default to 'main' if not specified
        if actual_scope_target not in ["main", "function_body"]:
            # If target is not a valid scope (e.g., "loop"), default to "main"
            actual_scope_target = "main"

        scope_config = {"target": actual_scope_target}
        if actual_scope_target == "function_body" and config.get("options", {}).get("function_name"):
            scope_config["options"] = {"function_name": config["options"]["function_name"]}

        target_body = _get_target_scope_blocks_and_ref(program_dict, scope_config)
        if target_body is None: return program_dict # Không tìm thấy phạm vi mục tiêu
        main_body = target_body # Đổi tên biến để dễ đọc, thực chất là target_body
        if len(main_body) < 2:
            print("   - ⚠️ Không đủ khối lệnh trong main để tạo lỗi 'sequence_error'.")
            return program_dict

        # [CẢI TIẾN] Ưu tiên hoán đổi hai khối có loại khác nhau để tạo lỗi rõ ràng.
        # 1. Tìm tất cả các cặp chỉ số (index) của các khối có loại khác nhau.
        different_type_pairs = []
        for i in range(len(main_body)):
            for j in range(i + 1, len(main_body)):
                if main_body[i].get('type') != main_body[j].get('type'):
                    different_type_pairs.append((i, j))
        
        bug_options = config.get("options", {})
        block_type_to_swap = bug_options.get("block_type_to_swap") # Ví dụ: "maze_repeat"

        idx1, idx2 = -1, -1
        if different_type_pairs:
            # 2. Nếu có các cặp khác loại, chọn ngẫu nhiên một cặp để hoán đổi.
            # Đặc biệt ưu tiên hoán đổi khối đầu tiên với một khối khác loại.
            # [CẢI TIẾN] Nếu có block_type_to_swap, ưu tiên hoán đổi nó.
            if block_type_to_swap:
                target_indices = [i for i, block in enumerate(main_body) if block.get("type") == block_type_to_swap]
                if len(target_indices) > 0:
                    idx1 = random.choice(target_indices)
                    idx2 = random.choice([i for i in range(len(main_body)) if i != idx1])
                    print(f"      -> Bug 'sequence_error': Ưu tiên hoán đổi khối '{block_type_to_swap}'.")
            first_block_pairs = [pair for pair in different_type_pairs if pair[0] == 0]
            if first_block_pairs: # Original logic for first block
                idx1, idx2 = random.choice(first_block_pairs)
                print("      -> Bug 'sequence_error': Ưu tiên hoán đổi khối đầu tiên với khối khác loại.")
            else:
                idx1, idx2 = random.choice(different_type_pairs)
        else:
            # 3. Nếu tất cả các khối đều cùng loại (ví dụ: toàn moveForward),
            # thì quay lại logic hoán đổi ngẫu nhiên như cũ.
            idx1, idx2 = random.sample(range(len(main_body)), 2)

        # Thực hiện hoán đổi
        main_body[idx1], main_body[idx2] = main_body[idx2], main_body[idx1]
        print(f"      -> Bug 'sequence_error': Hoán đổi khối lệnh ở vị trí {idx1} và {idx2} trong main.")
        return program_dict

class MissingBlockBug(BaseBugStrategy):
    """
    1.1. Lỗi Tuần Tự: Thiếu Khối Lệnh (Missing Block Error)
    Xóa một khối lệnh ngẫu nhiên.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Determine the actual scope to search within
        actual_scope_target = config.get("target", "main") # Default to 'main' if not specified
        if actual_scope_target not in ["main", "function_body"]:
            # If target is not a valid scope (e.g., "loop"), default to "main"
            actual_scope_target = "main"

        scope_config = {"target": actual_scope_target}
        if actual_scope_target == "function_body" and config.get("options", {}).get("function_name"):
            scope_config["options"] = {"function_name": config["options"]["function_name"]}
        
        function_name = scope_config.get("options", {}).get("function_name") # Get function_name from the refined scope_config

        # Lấy tham chiếu đến danh sách khối lệnh trong phạm vi mục tiêu
        target_blocks_list_ref = _get_target_scope_blocks_and_ref(program_dict, scope_config)
        if target_blocks_list_ref is None:
            print(f"   - ⚠️ Không tìm thấy phạm vi mục tiêu '{actual_scope_target}' (hàm: {function_name}) để xóa khối lệnh.")
            return program_dict

        # Tìm tất cả các khối có thể xóa trong phạm vi mục tiêu (bao gồm cả các khối lồng nhau)
        # Chúng ta cần một danh sách các tuple (tham chiếu_đến_list_cha, index_trong_list_cha, khối_con)
        removable_blocks_info = []
        def _collect_removable_info(current_list: List[Dict], parent_list_ref: List[Dict]):
            for i, block in enumerate(current_list):
                removable_blocks_info.append({'parent_list_ref': parent_list_ref, 'index': i, 'block': block})
                if "body" in block and isinstance(block["body"], list): _collect_removable_info(block["body"], block["body"])
                if "orelse" in block and isinstance(block["orelse"], list): _collect_removable_info(block["orelse"], block["orelse"])
        _collect_removable_info(target_blocks_list_ref, target_blocks_list_ref)

        if not removable_blocks_info:
            print(f"   - ⚠️ Không tìm thấy khối lệnh nào có thể xóa trong phạm vi '{actual_scope_target}' (hàm: {function_name}).")
            return program_dict

        # [MỚI] Xử lý trường hợp đặc biệt 'missing_function_call'
        bug_type_from_config = config.get("bug_type")
        if bug_type_from_config == "missing_function_call":
            call_blocks = [item for item in removable_blocks_info if item['block'].get("type") == "CALL"]
            if call_blocks:
                target_item = random.choice(call_blocks)
                removed_block = target_item['parent_list_ref'].pop(target_item['index'])
                print(f"      -> Bug 'missing_function_call': Đã xóa khối gọi hàm '{removed_block.get('name')}' từ phạm vi '{actual_scope_target}'.")
                return program_dict

        # [REWRITTEN] Ưu tiên tìm và xóa khối được chỉ định trong config trên TOÀN BỘ chương trình
        block_type_to_remove = config.get("options", {}).get("block_type_to_remove")
        if block_type_to_remove:
            specific_blocks = [
                item for item in removable_blocks_info
                if (
                    # [SỬA LỖI] Nếu yêu cầu xóa "turn" hoặc "any_turn", tìm bất kỳ khối "maze_turn" nào.
                    (block_type_to_remove in ['turn', 'any_turn'] and
                     item['block'].get("type") == "maze_turn")
                    or
                    # [CŨ] Nếu yêu cầu xóa "turnLeft"/"turnRight" cụ thể.
                    (('turn' in block_type_to_remove and block_type_to_remove != 'turn') and
                     item['block'].get("type") == "maze_turn" and
                     item['block'].get("direction") == block_type_to_remove)
                    or
                    # [SỬA LỖI] Logic cho các khối khác, xử lý đúng các trường hợp tên
                    # như 'collect' hoặc 'collectItem'.
                    # Nếu block_type_to_remove đã chứa 'maze_', dùng trực tiếp.
                    # Nếu không, thêm tiền tố 'maze_'.
                    # Xử lý trường hợp đặc biệt 'collectItem' -> 'maze_collect'.
                    (item['block'].get("type") == ('maze_collect' if block_type_to_remove == 'collectItem' else
                                                   block_type_to_remove if block_type_to_remove.startswith('maze_') else
                                                   f"maze_{block_type_to_remove}"))
                )
            ]
            if specific_blocks:
                target_item = random.choice(specific_blocks)
                removed_block = target_item['parent_list_ref'].pop(target_item['index'])
                print(f"      -> Bug 'missing_block': Đã xóa khối được chỉ định '{removed_block.get('type')}' từ phạm vi '{actual_scope_target}'.")
                return program_dict
            else:
                print(f"   - ⚠️ Không tìm thấy khối loại '{block_type_to_remove}' để xóa trong phạm vi '{actual_scope_target}'. Sẽ xóa một khối ngẫu nhiên.")

        # Nếu không có chỉ định hoặc không tìm thấy, quay về logic cũ: xóa một khối ngẫu nhiên
        target_item_to_remove = random.choice(removable_blocks_info)
        removed_block = target_item_to_remove['parent_list_ref'].pop(target_item_to_remove['index'])
        print(f"      -> Bug 'missing_block': Đã xóa khối ngẫu nhiên '{removed_block.get('type')}'")
        return program_dict

class IncorrectLoopCountBug(BaseBugStrategy):
    """
    1.2. Lỗi Cấu Hình: Sai Số Lần Lặp (Incorrect Loop Count)
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Determine the actual scope to search within
        actual_scope_target = config.get("target", "main") # Default to 'main' if not specified
        if actual_scope_target not in ["main", "function_body"]:
            # If target is not a valid scope (e.g., "loop"), default to "main"
            actual_scope_target = "main"

        scope_config = {"target": actual_scope_target}
        if actual_scope_target == "function_body" and config.get("options", {}).get("function_name"):
            scope_config["options"] = {"function_name": config["options"]["function_name"]}

        # Tìm tất cả các khối vòng lặp trong toàn bộ chương trình
        target_blocks_list = _get_target_scope_blocks_and_ref(program_dict, scope_config)
        if target_blocks_list is None: return program_dict

        all_loops = _find_blocks_recursively(target_blocks_list, lambda block: block.get("type") == "maze_repeat")

        if all_loops:
            # [SỬA LỖI] Đảm bảo chọn vòng lặp trong phạm vi đã chỉ định
            target_loop = random.choice(all_loops)
            original_num = target_loop.get("times", 1)
            # Tạo lỗi: +1 hoặc -1, đảm bảo không nhỏ hơn 1
            # Get the change_by value from bug_config options
            change_by = config.get("options", {}).get("change_by", random.choice([-1, 1]))
            bugged_num = original_num + change_by
            if bugged_num <= 0:
                bugged_num = original_num + 1 # Nếu trừ đi bị <= 0 thì cộng
            
            target_loop["times"] = bugged_num
            print(f"      -> Bug 'incorrect_loop_count': Thay đổi số lần lặp từ {original_num} thành {bugged_num} trong phạm vi '{actual_scope_target}'.")
        else:
            print("   - ⚠️ Không tìm thấy khối 'maze_repeat' để tạo lỗi.")
        return program_dict

class IncorrectParameterBug(BaseBugStrategy):
    """
    1.2. Lỗi Cấu Hình: Sai Tham Số (Incorrect Parameter)
    Ví dụ: rẽ sai hướng.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # [CẢI TIẾN] Logic này giờ xử lý 2 trường hợp:
        # Determine the actual scope to search within
        actual_scope_target = config.get("target", "main") # Default to 'main' if not specified
        if actual_scope_target not in ["main", "function_body", "function_call"]: # "function_call" is a special target for this bug
            actual_scope_target = "main"

        scope_config = {"target": actual_scope_target}
        if actual_scope_target == "function_body" and config.get("options", {}).get("function_name"):
            scope_config["options"] = {"function_name": config["options"]["function_name"]}
        
        bug_options = config.get("options", {}) # Keep original bug_options for specific block types
        function_name = bug_options.get("function_name")

        # 1. Thay đổi tham số của một khối (ví dụ: direction của maze_turn).
        # 2. Thay thế hoàn toàn một khối bằng khối khác (ví dụ: jump -> moveForward).
        
        # [REWRITTEN] Logic to handle missing 'from' and 'to' for turn blocks
        bug_options = config.get("options", {}) or {} # Ensure bug_options is a dict
        from_block_type = bug_options.get("from") 
        to_block_type = bug_options.get("to")

        # If 'from' and 'to' are not provided, try to create a default turn bug
        if not from_block_type or not to_block_type:
            print("   - INFO: 'from'/'to' not in config. Attempting to create default turn bug.")
            target_blocks_list = _get_target_scope_blocks_and_ref(program_dict, scope_config)
            if target_blocks_list:
                turn_blocks = _find_blocks_recursively(target_blocks_list, lambda b: b.get("type") == "maze_turn")
                if turn_blocks:
                    target_turn = random.choice(turn_blocks)
                    original_direction = target_turn.get("direction")
                    if original_direction:
                        # Set from/to automatically
                        from_block_type = original_direction
                        to_block_type = "turnLeft" if original_direction == "turnRight" else "turnRight"
                        print(f"   - INFO: Auto-detected turn bug: from '{from_block_type}' to '{to_block_type}'.")
 
        if from_block_type and to_block_type:
            # [REWRITTEN] Logic tìm và thay thế khối, có xử lý trường hợp đặc biệt cho 'turn'
            
            # Điều kiện tìm kiếm:
            # - Nếu là khối 'turn', tìm type='maze_turn' VÀ direction khớp.
            # - Nếu là khối khác, tìm type='maze_{from_block_type}'.
            is_turn_bug = 'turn' in from_block_type
            # [MỚI] Thêm trường hợp đặc biệt cho jump
            is_jump_bug = from_block_type == 'jump'
            
            def find_condition(block):
                if is_turn_bug and block.get("type") == "maze_turn":
                    return block.get("type") == "maze_turn" and block.get("direction") == from_block_type
                elif is_jump_bug and block.get("type") == "maze_jump":
                    return block.get("type") == "maze_jump"
                else:
                    return block.get("type") == f"maze_{from_block_type}"

            # For "function_call" target, we need to search the main body.
            search_scope_for_blocks = program_dict.get("main") if actual_scope_target == "function_call" else \
                                      _get_target_scope_blocks_and_ref(program_dict, scope_config) # type: ignore

            # [FIX] Use the correct variable for the recursive search
            target_blocks_list = search_scope_for_blocks
            if search_scope_for_blocks is None: return program_dict
            possible_blocks = _find_blocks_recursively(target_blocks_list, find_condition)


            if possible_blocks:
                target_block = random.choice(possible_blocks)
                original_type = target_block.get("type")
                
                if is_turn_bug:
                    # Chỉ thay đổi direction, không thay đổi type
                    original_dir = target_block.get("direction")
                    target_block["direction"] = to_block_type
                    print(f"      -> Bug 'incorrect_parameter': Thay đổi hướng rẽ từ '{original_dir}' thành '{to_block_type}' trong phạm vi '{actual_scope_target}' (hàm: {function_name}).")
                elif is_jump_bug:
                    target_block["type"] = f"maze_{to_block_type}"
                    if "direction" in target_block: del target_block["direction"]
                    print(f"      -> Bug 'incorrect_parameter': Thay thế khối '{original_type}' bằng '{target_block['type']}' trong phạm vi '{actual_scope_target}' (hàm: {function_name}).")
                else:
                    target_block["type"] = f"maze_{to_block_type}"
                    if "direction" in target_block: del target_block["direction"]
                    print(f"      -> Bug 'incorrect_parameter': Thay thế khối '{original_type}' bằng '{target_block['type']}' trong phạm vi '{actual_scope_target}' (hàm: {function_name}).")
            else:
                print(f"   - ⚠️ Không tìm thấy khối loại '{from_block_type}' để tạo lỗi incorrect_parameter trong phạm vi '{actual_scope_target}' (hàm: {function_name}).")
        else:
            print("   - ⚠️ Cấu hình 'from' và 'to' không được cung cấp cho lỗi 'incorrect_parameter'.")
        return program_dict

class IncorrectMathExpressionBug(BaseBugStrategy):
    """
    1.3. Lỗi Dữ Liệu: Sai Biểu Thức Toán Học (Incorrect Math Expression)
    Thay đổi toán tử trong một khối `math_arithmetic`.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Determine the actual scope to search within
        actual_scope_target = config.get("target", "main") # Default to 'main' if not specified
        if actual_scope_target not in ["main", "function_body"]:
            # If target is not a valid scope, default to "main"
            actual_scope_target = "main"

        scope_config = {"target": actual_scope_target}
        if actual_scope_target == "function_body" and config.get("options", {}).get("function_name"):
            scope_config["options"] = {"function_name": config["options"]["function_name"]}

        # Tìm tất cả các khối có chứa biểu thức toán học
        target_blocks_list = _get_target_scope_blocks_and_ref(program_dict, scope_config)
        if target_blocks_list is None: return program_dict

        math_expr_blocks = _find_blocks_recursively(target_blocks_list, lambda block: block.get("type") == "maze_repeat_expression")
        # [MỚI] Cũng tìm trong các khối math_arithmetic trực tiếp (ví dụ: trong variables_set)
        math_expr_blocks.extend(_find_blocks_recursively(target_blocks_list, lambda block: block.get("type") == "math_arithmetic"))
        
        if math_expr_blocks:
            target_block = random.choice(math_expr_blocks)
            expression = target_block.get("expression")
            if expression and expression.get("type") == "math_arithmetic":
                original_op = expression.get("op", "ADD")
                # Chọn một toán tử khác để thay thế
                possible_ops = ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"]
                possible_ops.remove(original_op)
                bugged_op = random.choice(possible_ops)
                expression["op"] = bugged_op # type: ignore
                print(f"      -> Bug 'incorrect_math_expression': Thay đổi toán tử từ {original_op} thành {bugged_op} trong phạm vi '{actual_scope_target}'.")
            elif target_block.get("type") == "math_arithmetic": # Nếu là khối math_arithmetic trực tiếp
                original_op = target_block.get("op", "ADD")
                possible_ops = ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"]
                possible_ops.remove(original_op)
                bugged_op = random.choice(possible_ops)
                target_block["op"] = bugged_op # type: ignore
                print(f"      -> Bug 'incorrect_math_expression': Thay đổi toán tử từ {original_op} thành {bugged_op} trong phạm vi '{actual_scope_target}'.")
        else:
            print(f"   - ⚠️ Không tìm thấy khối 'maze_repeat_expression' hoặc 'math_arithmetic' để tạo lỗi trong phạm vi '{actual_scope_target}'.")
        return program_dict

class IncorrectInitialValueBug(BaseBugStrategy):
    """
    1.3. Lỗi Dữ Liệu: Sai Giá Trị Khởi Tạo (Incorrect Initial Value)
    Tìm một khối `variables_set` và thay đổi giá trị số của nó.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Determine the actual scope to search within
        actual_scope_target = config.get("target", "main") # Default to 'main' if not specified
        if actual_scope_target not in ["main", "function_body"]:
            # If target is not a valid scope (e.g., "variable"), default to "main"
            actual_scope_target = "main"

        scope_config = {"target": actual_scope_target}
        if actual_scope_target == "function_body" and config.get("options", {}).get("function_name"):
            scope_config["options"] = {"function_name": config["options"]["function_name"]}

        # Tìm tất cả các khối gán giá trị là một số
        target_blocks_list = _get_target_scope_blocks_and_ref(program_dict, scope_config)
        if target_blocks_list is None: return program_dict

        set_var_blocks = _find_blocks_recursively(target_blocks_list, lambda block: block.get("type") == "variables_set" and isinstance(block.get("value"), int))
        
        if set_var_blocks:
            # [SỬA LỖI] Đảm bảo chọn khối trong phạm vi đã chỉ định
            target_block = random.choice(set_var_blocks)
            original_value = target_block["value"]
            # Tạo lỗi: +1 hoặc -1, đảm bảo không nhỏ hơn 1
            # Get the change_by value from bug_config options
            change_by = config.get("options", {}).get("change_by", random.choice([-1, 1]))
            bugged_value = original_value + change_by
            if bugged_value <= 0:
                bugged_value = original_value + 1
            
            target_block["value"] = bugged_value
            print(f"      -> Bug 'incorrect_initial_value': Thay đổi giá trị khởi tạo của biến '{target_block.get('variable')}' từ {original_value} thành {bugged_value} trong phạm vi '{actual_scope_target}'.")
        else:
            print(f"   - ⚠️ Không tìm thấy khối 'variables_set' với giá trị số để tạo lỗi trong phạm vi '{actual_scope_target}'.")
        return program_dict

class WrongLogicInAlgorithmBug(BaseBugStrategy):
    """
    Lỗi logic trong một thuật toán phức tạp (ví dụ: Fibonacci).
    Thay đổi các biến trong phép toán để làm sai logic.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Tìm khối tính toán Fibonacci: b = temp + b
        # Determine the actual scope to search within
        actual_scope_target = config.get("target", "main") # Default to 'main' if not specified
        if actual_scope_target not in ["main", "function_body"]:
            # If target is not a valid scope, default to "main"
            actual_scope_target = "main"

        scope_config = {"target": actual_scope_target}
        if actual_scope_target == "function_body" and config.get("options", {}).get("function_name"):
            scope_config["options"] = {"function_name": config["options"]["function_name"]}

        target_blocks_list = _get_target_scope_blocks_and_ref(program_dict, scope_config)

        fibonacci_calc_blocks = _find_blocks_recursively(target_blocks_list, lambda block: block.get("type") == "variables_set" and isinstance(block.get("value"), dict) and block["value"].get("type") == "math_arithmetic" and block["value"].get("op") == "ADD")
        
        if fibonacci_calc_blocks:
            # [SỬA LỖI] Đảm bảo chọn khối trong phạm vi đã chỉ định
            target_block = fibonacci_calc_blocks[0] # Giả định chỉ có 1 khối
            math_expr = target_block["value"]
            original_vars = (math_expr.get("var_a"), math_expr.get("var_b"))

            # Tạo lỗi: thay vì b = temp + b, ta đổi thành b = temp + a
            # Giả định var_a là 'temp' và var_b là 'b'
            if original_vars[0] and original_vars[1]:
                math_expr["var_b"] = original_vars[0] # type: ignore
                print(f"      -> Bug 'wrong_logic_in_algorithm': Thay đổi phép toán từ "
                      f"'{original_vars[0]} + {original_vars[1]}' thành '{math_expr['var_a']} + {math_expr['var_b']}' trong phạm vi '{actual_scope_target}'.")
        else:
            print(f"   - ⚠️ Không tìm thấy khối tính toán thuật toán phù hợp để tạo lỗi trong phạm vi '{actual_scope_target}'.")
        return program_dict

class RedundantBlocksBug(BaseBugStrategy):
    """
    1.4. Lỗi Tối Ưu Hóa: Thừa Khối Lệnh (Redundant Blocks)
    [REWRITTEN] Chèn một khối lệnh thừa vào một vị trí ngẫu nhiên trong chương trình.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Determine the actual scope to search within
        actual_scope_target = config.get("target", "main") # Default to 'main' if not specified
        if actual_scope_target not in ["main", "function_body"]:
            # If target is not a valid scope, default to "main"
            actual_scope_target = "main"

        scope_config = {"target": actual_scope_target}
        if actual_scope_target == "function_body" and config.get("options", {}).get("function_name"):
            scope_config["options"] = {"function_name": config["options"]["function_name"]}

        # Lấy loại khối lệnh cần thêm từ config, mặc định là 'turnRight'
        block_type_to_add = config.get("options", {}).get("block_type_to_add", "turnRight") # Use original config for block_type_to_add
        function_name = config.get("options", {}).get("function_name")

        # Tạo khối lệnh thừa
        if "turn" in block_type_to_add:
            extra_block = {"type": "maze_turn", "direction": block_type_to_add}
        elif block_type_to_add.startswith("CALL:"): # [MỚI] Xử lý chèn lệnh gọi hàm
            extra_block = {"type": "CALL", "name": block_type_to_add.split(":", 1)[1]}
        else:
            extra_block = {"type": f"maze_{block_type_to_add}"}

        # Tìm một nơi để chèn khối lệnh (ưu tiên chương trình chính)
        target_body = _get_target_scope_blocks_and_ref(program_dict, scope_config)
        if target_body is not None and isinstance(target_body, list):
            # Chèn vào một vị trí ngẫu nhiên trong target_body
            insert_idx = random.randint(0, len(target_body))
            target_body.insert(insert_idx, extra_block)
            print(f"      -> Bug 'extra_block': Đã chèn khối '{block_type_to_add}' thừa vào vị trí {insert_idx} trong phạm vi '{actual_scope_target}' (hàm: {function_name}).")
        else:
            print(f"   - ⚠️ Không tìm thấy phạm vi mục tiêu '{actual_scope_target}' (hàm: {function_name}) để chèn khối lệnh thừa.")

        return program_dict
