# src/bug_generator/strategies/main_thread_bugs.py
import random
from typing import Any, Dict, List
from .base_strategy import BaseBugStrategy

def _find_blocks_recursively(program_part: List[Dict], condition: callable) -> List[Dict]:
    """Hàm helper để tìm tất cả các khối thỏa mãn một điều kiện trong cấu trúc chương trình."""
    found_blocks = []
    for block in program_part:
        if condition(block):
            found_blocks.append(block)
        # [SỬA LỖI] Đệ quy vào các khối lồng nhau (vòng lặp, if, v.v.)
        # Logic cũ chỉ tìm trong "body" của hàm, bỏ qua "body" của vòng lặp.
        if "body" in block and isinstance(block["body"], list):
            found_blocks.extend(_find_blocks_recursively(block["body"], condition))
        # [MỚI] Xử lý các nhánh khác của khối if/else
        if "orelse" in block and isinstance(block["orelse"], list):
            found_blocks.extend(_find_blocks_recursively(block["orelse"], condition))
    return found_blocks

class MisplacedBlocksBug(BaseBugStrategy):
    """
    1.1. Lỗi Tuần Tự: Sai Thứ Tự Khối Lệnh (Sequence Error)
    Hoán đổi vị trí của hai khối lệnh ngẫu nhiên trong chương trình chính.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        main_body = program_dict.get("main", [])
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

        idx1, idx2 = -1, -1
        if different_type_pairs:
            # 2. Nếu có các cặp khác loại, chọn ngẫu nhiên một cặp để hoán đổi.
            # Đặc biệt ưu tiên hoán đổi khối đầu tiên với một khối khác loại.
            first_block_pairs = [pair for pair in different_type_pairs if pair[0] == 0]
            if first_block_pairs:
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
        # [MỚI] Helper để tìm tất cả các body và khối lệnh có thể xóa
        def find_removable_blocks_and_bodies(program_part: List[Dict]):
            removable = []
            if len(program_part) > 1:
                for i, block in enumerate(program_part):
                    removable.append({'body': program_part, 'index': i, 'block': block})
            for block in program_part:
                if "body" in block and isinstance(block["body"], list):
                    removable.extend(find_removable_blocks_and_bodies(block["body"]))
            return removable

        all_bodies = [program_dict.get("main", [])]
        for proc_body in program_dict.get("procedures", {}).values():
            all_bodies.append(proc_body)

        all_removable_blocks = find_removable_blocks_and_bodies(program_dict.get("main", []))
        for proc_body in program_dict.get("procedures", {}).values():
            all_removable_blocks.extend(find_removable_blocks_and_bodies(proc_body))

        if not all_removable_blocks:
            print("   - ⚠️ Không tìm thấy nơi nào phù hợp để xóa khối lệnh (cần ít nhất 2 khối).")
            return program_dict

        # [REWRITTEN] Ưu tiên tìm và xóa khối được chỉ định trong config trên TOÀN BỘ chương trình
        block_type_to_remove = config.get("options", {}).get("block_type_to_remove")
        if block_type_to_remove:
            specific_blocks = [
                item for item in all_removable_blocks
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
                removed_block = target_item['body'].pop(target_item['index'])
                print(f"      -> Bug 'missing_block': Đã xóa khối được chỉ định '{removed_block.get('type')}' từ body của nó.")
                return program_dict
            else:
                print(f"   - ⚠️ Không tìm thấy khối loại '{block_type_to_remove}' để xóa. Sẽ xóa một khối ngẫu nhiên.")

        # Nếu không có chỉ định hoặc không tìm thấy, quay về logic cũ: xóa một khối ngẫu nhiên
        target_item_to_remove = random.choice(all_removable_blocks)
        removed_block = target_item_to_remove['body'].pop(target_item_to_remove['index'])
        print(f"      -> Bug 'missing_block': Đã xóa khối ngẫu nhiên '{removed_block.get('type')}'")
        return program_dict

class IncorrectLoopCountBug(BaseBugStrategy):
    """
    1.2. Lỗi Cấu Hình: Sai Số Lần Lặp (Incorrect Loop Count)
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Tìm tất cả các khối vòng lặp trong toàn bộ chương trình
        all_loops = _find_blocks_recursively(
            program_dict.get("main", []),
            lambda block: block.get("type") == "maze_repeat"
        )
        for proc_body in program_dict.get("procedures", {}).values():
            all_loops.extend(_find_blocks_recursively(
                proc_body,
                lambda block: block.get("type") == "maze_repeat"
            ))

        if all_loops:
            target_loop = random.choice(all_loops)
            original_num = target_loop.get("times", 1)
            # Tạo lỗi: +1 hoặc -1, đảm bảo không nhỏ hơn 1
            offset = random.choice([-1, 1])
            bugged_num = original_num + offset
            if bugged_num <= 0:
                bugged_num = original_num + 1 # Nếu trừ đi bị <= 0 thì cộng
            
            target_loop["times"] = bugged_num
            print(f"      -> Bug 'incorrect_loop_count': Thay đổi số lần lặp từ {original_num} thành {bugged_num}.")
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
        # 1. Thay đổi tham số của một khối (ví dụ: direction của maze_turn).
        # 2. Thay thế hoàn toàn một khối bằng khối khác (ví dụ: jump -> moveForward).
        
        bug_options = config.get("options", {})
        from_block_type = bug_options.get("from")
        to_block_type = bug_options.get("to")
 
        if from_block_type and to_block_type:
            # [REWRITTEN] Logic tìm và thay thế khối, có xử lý trường hợp đặc biệt cho 'turn'
            
            # Điều kiện tìm kiếm:
            # - Nếu là khối 'turn', tìm type='maze_turn' VÀ direction khớp.
            # - Nếu là khối khác, tìm type='maze_{from_block_type}'.
            is_turn_bug = 'turn' in from_block_type
            
            def find_condition(block):
                if is_turn_bug:
                    return block.get("type") == "maze_turn" and block.get("direction") == from_block_type
                else:
                    return block.get("type") == f"maze_{from_block_type}"

            possible_blocks = _find_blocks_recursively(program_dict.get("main", []), find_condition)
            for proc_body in program_dict.get("procedures", {}).values():
                possible_blocks.extend(_find_blocks_recursively(proc_body, find_condition))

            if possible_blocks:
                target_block = random.choice(possible_blocks)
                original_type = target_block.get("type")
                
                if is_turn_bug:
                    # Chỉ thay đổi direction, không thay đổi type
                    original_dir = target_block["direction"]
                    target_block["direction"] = to_block_type
                    print(f"      -> Bug 'incorrect_block': Thay đổi hướng rẽ từ '{original_dir}' thành '{to_block_type}'.")
                else:
                    # Thay đổi toàn bộ type của khối
                    target_block["type"] = f"maze_{to_block_type}"
                    if "direction" in target_block: del target_block["direction"]
                    print(f"      -> Bug 'incorrect_parameter': Thay thế khối '{original_type}' bằng '{target_block['type']}'.")
            else:
                print(f"   - ⚠️ Không tìm thấy khối loại 'maze_{from_block_type}' để tạo lỗi incorrect_block.")
        else:
            # Trường hợp 1: Thay đổi tham số (logic cũ cho maze_turn)
            all_turns = _find_blocks_recursively(
                program_dict.get("main", []),
                lambda block: block.get("type") == "maze_turn"
            )
            # (Có thể mở rộng để tìm trong procedures nếu cần)
            for proc_body in program_dict.get("procedures", {}).values():
                all_turns.extend(_find_blocks_recursively(
                    proc_body,
                    lambda block: block.get("type") == "maze_turn"
                ))
            
            if all_turns:
                target_turn = random.choice(all_turns)
                original_dir = target_turn.get("direction", "turnRight")
                bugged_dir = "turnLeft" if original_dir == "turnRight" else "turnRight"
                target_turn["direction"] = bugged_dir
                print(f"      -> Bug 'incorrect_parameter': Thay đổi hướng rẽ từ {original_dir} thành {bugged_dir}.")
            else:
                print("   - ⚠️ Không tìm thấy khối 'maze_turn' để tạo lỗi incorrect_parameter.")
 
        return program_dict

class IncorrectMathExpressionBug(BaseBugStrategy):
    """
    1.3. Lỗi Dữ Liệu: Sai Biểu Thức Toán Học (Incorrect Math Expression)
    Thay đổi toán tử trong một khối `math_arithmetic`.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Tìm tất cả các khối có chứa biểu thức toán học
        # Trong trường hợp này, nó nằm trong 'maze_repeat_expression'
        math_expr_blocks = _find_blocks_recursively(
            program_dict.get("main", []),
            lambda block: block.get("type") == "maze_repeat_expression"
        )
        for proc_body in program_dict.get("procedures", {}).values():
            math_expr_blocks.extend(_find_blocks_recursively(
                proc_body,
                lambda block: block.get("type") == "maze_repeat_expression"
            ))

        if math_expr_blocks:
            target_block = random.choice(math_expr_blocks)
            expression = target_block.get("expression")
            if expression and expression.get("type") == "math_arithmetic":
                original_op = expression.get("op", "ADD")
                # Chọn một toán tử khác để thay thế
                possible_ops = ["ADD", "SUBTRACT", "MULTIPLY", "DIVIDE"]
                possible_ops.remove(original_op)
                bugged_op = random.choice(possible_ops)
                expression["op"] = bugged_op
                print(f"      -> Bug 'incorrect_math_expression': Thay đổi toán tử từ {original_op} thành {bugged_op}.")
        else:
            print("   - ⚠️ Không tìm thấy khối 'maze_repeat_expression' để tạo lỗi.")
        return program_dict

class IncorrectInitialValueBug(BaseBugStrategy):
    """
    1.3. Lỗi Dữ Liệu: Sai Giá Trị Khởi Tạo (Incorrect Initial Value)
    Tìm một khối `variables_set` và thay đổi giá trị số của nó.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Tìm tất cả các khối gán giá trị là một số
        set_var_blocks = _find_blocks_recursively(
            program_dict.get("main", []),
            lambda block: (
                block.get("type") == "variables_set" and
                isinstance(block.get("value"), int)
            )
        )

        if set_var_blocks:
            target_block = random.choice(set_var_blocks)
            original_value = target_block["value"]
            # Tạo lỗi: +1 hoặc -1, đảm bảo không nhỏ hơn 1
            offset = random.choice([-1, 1])
            bugged_value = original_value + offset
            if bugged_value <= 0:
                bugged_value = original_value + 1
            
            target_block["value"] = bugged_value
            print(f"      -> Bug 'incorrect_initial_value': Thay đổi giá trị khởi tạo của biến '{target_block.get('variable')}' từ {original_value} thành {bugged_value}.")
        else:
            print("   - ⚠️ Không tìm thấy khối 'variables_set' với giá trị số để tạo lỗi.")
        return program_dict

class WrongLogicInAlgorithmBug(BaseBugStrategy):
    """
    Lỗi logic trong một thuật toán phức tạp (ví dụ: Fibonacci).
    Thay đổi các biến trong phép toán để làm sai logic.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Tìm khối tính toán Fibonacci: b = temp + b
        fibonacci_calc_blocks = _find_blocks_recursively(
            program_dict.get("main", []),
            lambda block: (
                block.get("type") == "variables_set" and
                isinstance(block.get("value"), dict) and
                block["value"].get("type") == "math_arithmetic" and
                block["value"].get("op") == "ADD"
            )
        )

        if fibonacci_calc_blocks:
            target_block = fibonacci_calc_blocks[0] # Giả định chỉ có 1 khối
            math_expr = target_block["value"]
            original_vars = (math_expr.get("var_a"), math_expr.get("var_b"))

            # Tạo lỗi: thay vì b = temp + b, ta đổi thành b = temp + a
            # Giả định var_a là 'temp' và var_b là 'b'
            if original_vars[0] and original_vars[1]:
                math_expr["var_b"] = original_vars[0] # Đổi var_b thành var_a
                print(f"      -> Bug 'wrong_logic_in_algorithm': Thay đổi phép toán từ "
                      f"'{original_vars[0]} + {original_vars[1]}' thành "
                      f"'{math_expr['var_a']} + {math_expr['var_b']}'.")
        else:
            print("   - ⚠️ Không tìm thấy khối tính toán thuật toán phù hợp để tạo lỗi.")
        return program_dict

class RedundantBlocksBug(BaseBugStrategy):
    """
    1.4. Lỗi Tối Ưu Hóa: Thừa Khối Lệnh (Redundant Blocks)
    [REWRITTEN] Chèn một khối lệnh thừa vào một vị trí ngẫu nhiên trong chương trình.
    """
    def apply(self, program_dict: Dict[str, Any], config: Dict) -> Dict[str, Any]:
        # Lấy loại khối lệnh cần thêm từ config, mặc định là 'turnRight'
        block_type_to_add = config.get("options", {}).get("block_type_to_add", "turnRight")

        # Tạo khối lệnh thừa
        if "turn" in block_type_to_add:
            extra_block = {"type": "maze_turn", "direction": block_type_to_add}
        else:
            extra_block = {"type": f"maze_{block_type_to_add}"}

        # Tìm một nơi để chèn khối lệnh (ưu tiên chương trình chính)
        main_body = program_dict.get("main")
        if main_body is not None and isinstance(main_body, list):
            # Chèn vào một vị trí ngẫu nhiên trong main_body
            insert_idx = random.randint(0, len(main_body))
            main_body.insert(insert_idx, extra_block)
            print(f"      -> Bug 'extra_block': Đã chèn khối '{block_type_to_add}' thừa vào vị trí {insert_idx} trong 'main'.")
        else:
            print("   - ⚠️ Không tìm thấy 'main' body (dạng list) để chèn khối lệnh thừa.")

        return program_dict
