import os
import sys
import time
import psutil
import cplex
from cplex.exceptions import CplexError
from cplex.callbacks import MIPInfoCallback

class MyIncumbentCallback(MIPInfoCallback):
    
    def __init__(self, env, model, var_list, var_map, start_time):
        super().__init__(env)
        self.var_list = var_list
        self.var_map = var_map
        self.start_time = start_time
        indices = model.variables.get_indices(self.var_list)
        self.name_to_idx = dict(zip(self.var_list, indices))

    def __call__(self):
        if not self.has_incumbent():
            return
        vals = self.get_incumbent_values()
        used_labels = set()
        for name in self.var_list:
            if vals[self.name_to_idx[name]] > 0.5:
                _, label_val = self.var_map[name]
                used_labels.add(label_val)
        
        print(f"\nNum labels used: {len(used_labels)}" )
        print(f"Current incumbent solution: {{" + ", ".join(map(str, sorted(used_labels))) + "}}")
        print(f"Time taken: {time.perf_counter() - self.start_time:.2f}s")

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
            parts = line.strip().split()
            if len(parts) > 2:
                domain.append(list(map(int, parts[2:])))
    return domain 

def read_var(file, domain):
    var = {}
    with open(file) as f:
        for line in f:
            parts = line.strip().split()
            if not parts: continue
            idx = int(parts[0])
            var[idx] = [int(parts[-2])] if len(parts) >= 4 else domain[int(parts[1])]
    return var

def build_optimized_mip(var, ctr_file):
    model = cplex.Cplex()
    model.objective.set_sense(model.objective.sense.minimize)
    
    # 1. Khai báo biến
    x_map = {} # (node_id, label_val) -> name
    all_labels = set()
    for i, vals in var.items():
        for v in vals:
            name = f"x_{i}_{v}"
            x_map[(i, v)] = name
            all_labels.add(v)
    
    l_map = {v: f"l_{v}" for v in sorted(all_labels)}
    x_names = list(x_map.values())
    l_names = list(l_map.values())
    
    # Thêm biến x_{i,v} và l_v
    model.variables.add(names=x_names, types=[model.variables.type.binary]*len(x_names))
    model.variables.add(names=l_names, types=[model.variables.type.binary]*len(l_names), obj=[1.0]*len(l_names))

    # 2. Xây dựng ràng buộc hàng loạt (Batch Processing)
    lin_expr, senses, rhs = [], [], []

    # Ràng buộc: Mỗi node chọn ĐÚNG 1 nhãn
    for i, vals in var.items():
        inds = [x_map[(i, v)] for v in vals]
        lin_expr.append(cplex.SparsePair(ind=inds, val=[1.0]*len(inds)))
        senses.append("E")
        rhs.append(1.0)

    # Ràng buộc: Liên kết x_{i,v} <= l_v (Nếu chọn nhãn v cho node i thì l_v phải bật)
    for (i, v), xname in x_map.items():
        lin_expr.append(cplex.SparsePair(ind=[xname, l_map[v]], val=[1.0, -1.0]))
        senses.append("L")
        rhs.append(0.0)

    # Ràng buộc: Khoảng cách (Distance Constraints)
    if os.path.exists(ctr_file):
        with open(ctr_file) as f:
            for line in f:
                parts = line.strip().split()
                if not parts or parts[0] == '\x00': continue
                u, v, dist = int(parts[0]), int(parts[1]), int(parts[4])
                if u not in var or v not in var: continue

                if '>' in parts:
                    for lu in var[u]:
                        bad_vjs = [x_map[(v, lv)] for lv in var[v] if abs(lu - lv) <= dist]
                        # Nếu chọn lu mà tất cả lv của v đều vi phạm -> Cấm lu
                        if len(bad_vjs) == len(var[v]):
                            lin_expr.append(cplex.SparsePair(ind=[x_map[(u, lu)]], val=[1.0]))
                            senses.append("E"); rhs.append(0.0)
                        else:
                            for v_name in bad_vjs:
                                lin_expr.append(cplex.SparsePair(ind=[x_map[(u, lu)], v_name], val=[1.0, 1.0]))
                                senses.append("L"); rhs.append(1.0)

                elif '=' in parts:
                    for lu in var[u]:
                        allowed = [x_map[(v, lv)] for lv in var[v] if abs(lu - lv) == dist]
                        # Nếu không có lv nào thỏa mãn -> Cấm lu
                        if not allowed:
                            lin_expr.append(cplex.SparsePair(ind=[x_map[(u, lu)]], val=[1.0]))
                            senses.append("E"); rhs.append(0.0)
                        else:
                            # Logic: x_u,lu <= sum(x_v,lv_allowed)
                            lin_expr.append(cplex.SparsePair(ind=[x_map[(u, lu)]] + allowed, 
                                                            val=[1.0] + [-1.0]*len(allowed)))
                            senses.append("L"); rhs.append(0.0)

    # Thêm hàng vạn ràng buộc vào model chỉ với 1 lần gọi hàm
    model.linear_constraints.add(lin_expr=lin_expr, senses=senses, rhs=rhs)
    return model, x_map

def main():
    start_time = time.perf_counter()
    if len(sys.argv) < 2:
        print("Use: python mip_optimized.py <folder_name>")
        return
    
    dataset_folder = os.path.join("dataset", sys.argv[1])
    files = get_file_names(dataset_folder)
    
    domain = read_domain(files["domain"])
    var_data = read_var(files["var"], domain)

    print(f"--- Building MIP model for {len(var_data)} variables ---")
    model, x_map = build_optimized_mip(var_data, files["ctr"])
    
    # Cấu hình Callback
    x_list = list(x_map.values())
    reverse_x_map = {v: k for k, v in x_map.items()}
    model.register_callback(lambda env: MyIncumbentCallback(env, model, x_list, reverse_x_map, start_time))

    # Tham số CPLEX để tối ưu tốc độ
    model.parameters.mip.tolerances.mipgap.set(0.0)  # Tìm tối ưu tuyệt đối
    model.parameters.preprocessing.reduce.set(3)    # Tiền xử lý mạnh tay
    model.parameters.threads.set(0)                 # Sử dụng toàn bộ nhân CPU

    print("--- Solving with CPLEX MIP ---")
    try:
        model.solve()
        
        # Trích xuất lời giải
        vals = model.solution.get_values()
        names = model.variables.get_names()
        assignment = {}
        for n, v in zip(names, vals):
            if n.startswith('x_') and v > 0.5:
                node_id, label_val = reverse_x_map[n]
                assignment[node_id] = label_val
        
        print("\n" + "="*30)
        print("FINAL INCUMBENT SOLUTION:")
        sorted_res = [assignment[i] for i in sorted(assignment.keys())]
        print("{" + ", ".join(map(str, sorted_res)) + "}")
        print(f"Number of labels used: {len(set(assignment.values()))}")
        
    except CplexError:
        print("No solution found or the problem is infeasible.")

    print(f"Total time: {time.perf_counter() - start_time:.2f}s")
    print(f"Memory used: {psutil.Process(os.getpid()).memory_info().rss / 1024**2:.2f} MB")
    print("="*30)

if __name__ == "__main__":
    main()