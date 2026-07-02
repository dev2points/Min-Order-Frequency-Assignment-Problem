import os
import sys
import psutil
import time
from docplex.cp.model import CpoModel

def get_file_names(dataset_folder):
    base = os.path.basename(dataset_folder)
    if base.lower().startswith(("graph", "tud")):
        return {
            "domain": os.path.join(dataset_folder, "dom.txt"),
            "var": os.path.join(dataset_folder, "var.txt"),
            "ctr": os.path.join(dataset_folder, "ctr.txt")
        }
    elif base.lower().startswith("scen"):
        return {
            "domain": os.path.join(dataset_folder, "DOM.TXT"),
            "var": os.path.join(dataset_folder, "VAR.TXT"),
            "ctr": os.path.join(dataset_folder, "CTR.TXT")
        }
    else:
        raise ValueError("Not a valid dataset: " + dataset_folder)

def read_domain(file):
    domain = []
    with open(file) as f:
        for line in f:
            line = line.strip()
            if not line or line == '\x00': continue
            parts = line.split()
            # Giả sử format: ID n v1 v2 ... vn
            values = list(map(int, parts[2:]))
            domain.append(values)
    return domain 

def read_var(file, domain):
    var = {}
    with open(file) as f:
        for line in f:
            parts = line.strip().split()
            if not parts:
                continue
            idx = int(parts[0])
            if len(parts) >= 4:
                domain_idx = int(parts[1])
                if int(parts[-2]) not in domain[domain_idx]:
                    print(f"Warning: variable {idx} has assigned label {parts[-2]} that is not in the domain {domain_idx}.")
                    return None
                else:
                    var[idx] = [int(parts[-2])]
            else:
                var[idx] = domain[int(parts[1])]
    return var # domain subset for each variable


def build_fast_cp_model(var, ctr_file):
    mdl = CpoModel()
    mdl.add_parameters(LogVerbosity="Terse")


    # 1. Tạo biến nguyên với miền giá trị RỜI RẠC
    # node_vars[i] chỉ nhận các giá trị có trong list var[i]
    node_vars = {}
    for i, vals in var.items():
        node_vars[i] = mdl.integer_var(domain=vals, name=f"node_{i}")

    # 2. Đọc và thiết lập ràng buộc khoảng cách
    with open(ctr_file) as f:
        for line in f:
            line = line.strip()
            if not line or line == '\x00': continue
            parts = line.split()
            
            u, v = int(parts[0]), int(parts[1])
            if u not in node_vars or v not in node_vars: continue
            
            distance = int(parts[4])
            
            # Sử dụng hàm hiệu tuyệt đối của CP Optimizer
            # Biểu thức này cực kỳ mạnh vì nó thực hiện lọc miền giá trị trực tiếp
            diff = mdl.abs(node_vars[u] - node_vars[v])
            
            if '>' in parts:
                mdl.add(diff > distance)
            elif '=' in parts:
                mdl.add(diff == distance)

    # 3. Hàm mục tiêu: Tối thiểu hóa số lượng nhãn khác nhau (Graph Coloring logic)
    # Đây là hàm "Global Constraint" giúp solver hội tụ cực nhanh
    all_vars = [node_vars[i] for i in sorted(node_vars.keys())]
    obj = mdl.count_different(all_vars)
    
    mdl.add(mdl.minimize(obj))

    return mdl, node_vars

def main():
    start_time = time.perf_counter()
    if len(sys.argv) < 2:
        print("Usage: python cp_fast.py <dataset_folder>")
        return

    dataset_path = os.path.join("dataset", sys.argv[1])
    try:
        files = get_file_names(dataset_path)
    except ValueError as e:
        print(e)
        return

    # Bước 1: Đọc dữ liệu
    domain_data = read_domain(files["domain"])
    var_data = read_var(files["var"], domain_data)
    if var_data is None:
        print("Cannot find solution!")
        print(f"Time taken: {time.perf_counter() - start_time:.5f} seconds")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")
        return

    # Bước 2: Xây dựng mô hình
    print(f"--- Building model for {len(var_data)} variables ---")
    mdl, node_vars = build_fast_cp_model(var_data, files["ctr"])

    # Bước 3: Giải bài toán
    print("--- Solving with CP Optimizer (Integer Mode) ---")
    # LogVerbosity="Terse" để ẩn các log trung gian, chỉ hiện kết quả tốt dần lên
    result = mdl.solve() 

    if result is None:
        print("No solution found (Result is None).")
        return

    status = result.get_solve_status()
    if status not in ("Optimal", "Feasible"):
        print("No valid solution:", status)
        print(f"Total time: {time.perf_counter() - start_time:.5f}s")
        process = psutil.Process(os.getpid())
        print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")
        return
    
    # Bước 4: Xuất kết quả
    if result:
        print("\n" + "="*30)
        print("OPTIMAL SOLUTION:")
        assignment = {i: result.get_value(node_vars[i]) for i in node_vars}
        
        # In dãy nhãn theo thứ tự ID node
        result_list = [assignment[i] for i in sorted(assignment.keys())]
        print(f"Label list: {result_list}")
        
        unique_labels = set(assignment.values())
        print(f"Number of labels used: {len(unique_labels)}")
        print(f"Specific labels: {sorted(list(unique_labels))}")
        print("="*30)
    else:
        print("Cannot find a solution.")

    # Thông số hệ thống
    end_time = time.perf_counter()
    process = psutil.Process(os.getpid())
    print(f"Total time: {end_time - start_time:.5f}s")
    print(f"Memory used: {process.memory_info().rss / 1024**2:.5f} MB")

if __name__ == "__main__":
    main()