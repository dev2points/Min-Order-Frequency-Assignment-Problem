# Min-Order-Frequency Assignment Problem

This repository contains multiple implementations for the Min-Order-Frequency Assignment Problem using:

- Gurobi
- CPLEX CP
- CPLEX MIP
- SAT (DSE and POSE)

The project supports running experiments with and without preprocessing.

## 1. Clone The Repository

```bash
git clone <https://github.com/dev2points/Min-Order-Frequency-Assignment-Problem.git>
cd Min-Order-Frequency-Assignment-Problem
```


## 2. Create Python Environment

Use Python 3.10 (recommended).

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python3.10 -m pip install --upgrade pip
```

## 3. Install Required Python Packages

Install common dependencies first:

```bash
python3.10 -m pip install psutil python-sat
```

Install solver-specific Python APIs depending on what you want to run:

```bash
# For Gurobi
python3.10 -m pip install gurobipy

# For CPLEX CP
python3.10 -m pip install docplex

# For CPLEX MIP (requires IBM CPLEX Python API)
# Usually available after installing IBM CPLEX Optimization Studio.
# Example (path may differ on your machine):
# python3.10 -m pip install /opt/ibm/ILOG/CPLEX_Studio2211/cplex/python/3.10/x86-64_linux
```

## 4. Install External Solvers

Some methods require commercial solvers installed and licensed:

- Gurobi: install Gurobi and activate license.
- CPLEX: install IBM CPLEX Optimization Studio (for `cplex` and `docplex.cp`).

SAT methods use PySAT and the bundled SAT backends (for example `cadical195`) via Python package.

## 5. Make Scripts Executable (Linux)

```bash
chmod +x Gurobi/auto.sh Gurobi/runlim
chmod +x CPLEX/CP/auto.sh CPLEX/CP/runlim
chmod +x CPLEX/MIP/auto.sh CPLEX/MIP/runlim
chmod +x SAT/DSE/auto.sh SAT/DSE/runlim
chmod +x SAT/POSE/auto.sh SAT/POSE/runlim
chmod +x SAT/POSE/*.sh
```

## 6. Run A Quick Single-Instance Test

Use one dataset instance first (example: `graph01`) to verify setup.

### Gurobi

```bash
cd Gurobi
python3 main.py graph01
```

### CPLEX CP

```bash
cd CPLEX/CP
python3 cp.py graph01
```

### CPLEX MIP

```bash
cd CPLEX/MIP
python3 mip.py graph01
```

### SAT DSE
####    DSE+INCSC

```bash
cd SAT/DSE
python3 pairwise.py graph01 assumptions
```

### SAT POSE

```bash
cd SAT/POSE
```
#### POSE+INCSC
```bash
python3 main.py graph01 nsc assumptions cadical195
```
#### POSE+INC
```bash
python3 main.py graph01 tot assumptions cadical195
```

Arguments for `SAT/POSE/main.py`:

- `strategy`: `nsc`, `sc`, `tot`, `nsc_reduced`, `sc_reduced`
- `sat_type`: `assumptions` or `incremental`
- `solver`: for example `cadical195` or `glucose4`

## 7. Run Full Experiments

Each module has `auto.sh` for batch runs over all instances with and without preprocessing.

### Gurobi

```bash
cd Gurobi
./auto.sh
```

### CPLEX

```bash
cd CPLEX/MIP
./auto.sh

cd ../CP
./auto.sh
```

### SAT DSE

```bash
cd SAT/DSE
./auto.sh
```

### SAT POSE

```bash
cd SAT/POSE
./auto.sh
```

`SAT/POSE/auto.sh` calls:

- `nsc_assumptions.sh`
- `tot_assumptions.sh`
- `nsc_assumptions_no_preprocessing.sh`
- `tot_assumptions_no_preprocessing.sh`

## 8. Datasets
Dataset can be found in the `dataset/`  or
each solver folder has its own `dataset/` directory.

Supported instance names include:

- `graph01` ... `graph14`
- `scen01` ... `scen11`
- `TUD200.1` ... `TUD200.5`
- `TUD916.1` ... `TUD916.5`

## 9. Results

Logs and outputs are written under each solver's `results/` directory, for example:

- `Gurobi/results/`
- `CPLEX/CP/results/`
- `CPLEX/MIP/results/`
- `SAT/POSE/results/`

You also have consolidated folders under `Result/`.

## 10. Common Issues

1. `ModuleNotFoundError: gurobipy`
Install Gurobi Python API and confirm license is active.

2. `ModuleNotFoundError: cplex` or CP Optimizer errors
Install IBM CPLEX Optimization Studio and Python bindings.

3. Permission denied on `runlim` or shell scripts
Run the `chmod +x ...` commands in Section 5.

4. SAT solver name not available
Use `cadical195` or `glucose4` as shown above.

