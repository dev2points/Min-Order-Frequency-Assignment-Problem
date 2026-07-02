# Min-Order-Frequency Assignment Problem

This repository contains several implementations of the Min-Order-Frequency Assignment Problem, including Gurobi, CPLEX CP, CPLEX MIP, CPSAT, SAT-based models, EvalMaxSAT, and MaxSAT-RC2 variants. Each solver family has its own source code, dataset copy, and result/log layout.

## Repository Structure

The shared instance library lives in [Datasets/](Datasets/), while each runnable module also keeps a local `dataset/` folder. Generated outputs are collected under [Results/](Results/), split into `pre_processing/` and `no_pre_processing/` runs.

| Area | Source code | Datasets | Results and logs |
| --- | --- | --- | --- |
| Gurobi | [Gurobi/main.py](Gurobi/main.py), [Gurobi/main_no.py](Gurobi/main_no.py) | [Gurobi/dataset/](Gurobi/dataset/) | Module-local logs under [Gurobi/results/pre_processing/](Gurobi/results/pre_processing/) and [Gurobi/results/no_pre_processing/](Gurobi/results/no_pre_processing/) |
| CPLEX CP | [CPLEX/CP/cp.py](CPLEX/CP/cp.py), [CPLEX/CP/cp_no.py](CPLEX/CP/cp_no.py) | [CPLEX/CP/dataset/](CPLEX/CP/dataset/) | Module-local logs under [CPLEX/CP/results/preprocessing/](CPLEX/CP/results/preprocessing/) and [CPLEX/CP/results/no_preprocessing/](CPLEX/CP/results/no_preprocessing/) |
| CPLEX MIP | [CPLEX/MIP/mip.py](CPLEX/MIP/mip.py), [CPLEX/MIP/mip_no.py](CPLEX/MIP/mip_no.py) | [CPLEX/MIP/dataset/](CPLEX/MIP/dataset/) | Module-local logs under [CPLEX/MIP/results/preprocessing/](CPLEX/MIP/results/preprocessing/) and [CPLEX/MIP/results/no_preprocessing/](CPLEX/MIP/results/no_preprocessing/) |
| CPSAT | [CPSAT/main.py](CPSAT/main.py), [CPSAT/main_no.py](CPSAT/main_no.py), [CPSAT/common.py](CPSAT/common.py) | [CPSAT/dataset/](CPSAT/dataset/) | Module-local logs under [CPSAT/results/preprocessing/](CPSAT/results/preprocessing/) and [CPSAT/results/no_preprocessing/](CPSAT/results/no_preprocessing/) |
| SAT DSE | [SAT/DSE/pairwise.py](SAT/DSE/pairwise.py), [SAT/DSE/pairwise_no_preprocessing.py](SAT/DSE/pairwise_no_preprocessing.py) | [SAT/DSE/dataset/](SAT/DSE/dataset/) | Module-local logs under [SAT/DSE/results/preprocessing/](SAT/DSE/results/preprocessing/) and [SAT/DSE/results/no_preprocessing/](SAT/DSE/results/no_preprocessing/) |
| SAT POSE | [SAT/POSE/main.py](SAT/POSE/main.py), [SAT/POSE/main_no_preprocessing.py](SAT/POSE/main_no_preprocessing.py) | [SAT/POSE/dataset/](SAT/POSE/dataset/) | Module-local logs under [SAT/POSE/results/preprocessing/INC/](SAT/POSE/results/preprocessing/INC/), [SAT/POSE/results/no_preprocessing/INC/](SAT/POSE/results/no_preprocessing/INC/), [SAT/POSE/results/preprocessing/INCSC/](SAT/POSE/results/preprocessing/INCSC/), and [SAT/POSE/results/no_preprocessing/INCSC/](SAT/POSE/results/no_preprocessing/INCSC/) |
| EvalMaxSAT | [EvalMaxSAT/evalmaxsat.py](EvalMaxSAT/evalmaxsat.py), [EvalMaxSAT/evalmaxsat_no_processing.py](EvalMaxSAT/evalmaxsat_no_processing.py), [EvalMaxSAT/extract_evalmaxsat_stats.py](EvalMaxSAT/extract_evalmaxsat_stats.py) | [EvalMaxSAT/dataset/](EvalMaxSAT/dataset/) | Logs under [EvalMaxSAT/results/processing/pipeline/](EvalMaxSAT/results/processing/pipeline/) and [EvalMaxSAT/results/no_preprocessing/pipeline/](EvalMaxSAT/results/no_preprocessing/pipeline/) |
| MaxSAT-RC2 | [MaxSAT-RC2/main.py](MaxSAT-RC2/main.py), [MaxSAT-RC2/main_no_processing.py](MaxSAT-RC2/main_no_processing.py) | [MaxSAT-RC2/dataset/](MaxSAT-RC2/dataset/) | Logs under [MaxSAT-RC2/results/processing/](MaxSAT-RC2/results/processing/) and [MaxSAT-RC2/results/no_processing/](MaxSAT-RC2/results/no_processing/) |

## Installation

Use Python 3.10 if possible.

```bash
python3.10 -m venv .venv
source .venv/bin/activate
python3.10 -m pip install --upgrade pip
```

Install the common Python dependencies first:

```bash
python3.10 -m pip install psutil python-sat
```

Install solver-specific Python packages as needed:

```bash
# Gurobi
python3.10 -m pip install gurobipy

# CPLEX CP / docplex.cp
python3.10 -m pip install docplex

# CPLEX MIP
# Install IBM CPLEX Optimization Studio, then install the matching Python API
# from the CPLEX installation path for your platform.
```

External solver requirements:

- Gurobi requires a working Gurobi installation and license.
- CPLEX CP and CPLEX MIP require IBM CPLEX Optimization Studio.
- SAT, EvalMaxSAT, and MaxSAT-RC2 workflows use PySAT together with a supported SAT backend such as `cadical195` or `glucose4`.

If you are on Linux, make the helper scripts executable once:

```bash
chmod +x Gurobi/*.sh Gurobi/runlim
chmod +x CPLEX/CP/*.sh CPLEX/CP/runlim
chmod +x CPLEX/MIP/*.sh CPLEX/MIP/runlim
chmod +x CPSAT/*.sh CPSAT/runlim
chmod +x SAT/DSE/*.sh SAT/DSE/runlim
chmod +x SAT/POSE/*.sh SAT/POSE/runlim
chmod +x EvalMaxSAT/*.sh EvalMaxSAT/runlim
chmod +x MaxSAT-RC2/*.sh MaxSAT-RC2/runlim
```

## How To Run

Start with a single instance such as `graph01` or `scen04` to verify the setup.

### Gurobi

```bash
cd Gurobi
python3 main.py graph01
python3 main_no.py graph01
```

### CPLEX CP

```bash
cd CPLEX/CP
python3 cp.py graph01
python3 cp_no.py graph01
```

### CPLEX MIP

```bash
cd CPLEX/MIP
python3 mip.py graph01
python3 mip_no.py graph01
```

### CPSAT

```bash
cd CPSAT
python3 main.py graph01
python3 main.py graph01 60
python3 main_no.py graph01
```

### SAT DSE
####    DSE+INCSC

```bash
cd SAT/DSE
python3 pairwise.py graph01 nsc assumptions cadical195
python3 pairwise_no_preprocessing.py graph01 nsc assumptions cadical195
```

### SAT POSE

```bash
cd SAT/POSE
```
#### POSE+INCSC
```bash
python3 main.py graph01 nsc assumptions cadical195
python3 main_no_preprocessing.py graph01 nsc assumptions cadical195
```
#### POSE+INC
```bash
python3 main.py graph01 tot assumptions cadical195
```

Supported `SAT/POSE` arguments:

- `strategy`: `nsc`, `sc`, `tot`, `nsc_reduced`, `sc_reduced`
- `sat_type`: `assumptions` or `incremental`
- `solver`: for example `cadical195` or `glucose4`

### EvalMaxSAT

```bash
cd EvalMaxSAT
python3 evalmaxsat.py scen04 POSE
python3 evalmaxsat_no_processing.py scen04 POSE
```

Other supported encodings include `DSE` and `CARD`. For `CARD`, pass at least one encoding id, for example `python3 evalmaxsat.py scen04 CARD 1 1`.

### MaxSAT-RC2

```bash
cd MaxSAT-RC2
python3 main.py graph01 DSE
python3 main_no_processing.py graph01 DSE
```

For `MaxSAT-RC2`, the second argument selects the encoding method. The script also accepts optional encoding ids for `DSE` and `CARD`-style runs.

## Batch Runs

Each solver folder includes shell wrappers for running the full benchmark set.

Typical usage:

```bash
cd Gurobi && ./auto.sh
cd CPLEX/CP && ./auto.sh
cd CPLEX/MIP && ./auto.sh
cd CPSAT && ./auto.sh
cd SAT/DSE && ./auto.sh
cd SAT/POSE && ./auto.sh
cd EvalMaxSAT && ./POSE.sh
cd EvalMaxSAT && ./POSEno.sh
cd EvalMaxSAT && ./DSE.sh
cd EvalMaxSAT && ./DSEno.sh
cd MaxSAT-RC2 && ./auto.sh
```

Some folders also provide no-preprocessing variants such as `auto_no.sh`, `DSEno.sh`, `POSEno.sh`, or `*_no.sh` scripts for the same instance sets.
EvalMaxSAT uses `POSEno.sh` and `DSEno.sh` for the no-preprocessing variants, while SAT/POSE uses `INC_no.sh` and `INCSC_no.sh`.

## Datasets

Supported instance families include:

- `graph01` ... `graph14`
- `scen01` ... `scen11`
- `TUD200.1` ... `TUD200.5`
- `TUD916.1` ... `TUD916.5`

Each module reads from its local `dataset/` folder, which mirrors the shared contents in [Datasets/](Datasets/).

The CALMA benchmark instances documented by the source page at [FAP CALMA](https://fap.zib.de/problems/#CALMA) come from the EUCLID CALMA project. The page describes two main benchmark families: 11 CELAR instances, 14 GRAPH instances and 10 DUTest instances, covering minimum order, minimum span, and minimum interference variants.

Each CALMA instance is distributed in four text files:

- `var.txt` for communication links
- `dom.txt` for frequency domains
- `ctr.txt` for constraints
- `cst.txt` for the optimization criteria

The CALMA page also notes that the instances contain distance and equality constraints, and that the equality structure can sometimes be used to reduce the problem size.

## Results And Logs

The runnable scripts write logs into module-local `results/` directories. The top-level [Results/](Results/) tree contains consolidated example outputs from prior runs.

- `Gurobi/results/pre_processing/` and `Gurobi/results/no_pre_processing/` contain the Gurobi logs.
- `CPLEX/CP/results/preprocessing/` and `CPLEX/CP/results/no_preprocessing/` contain the CPLEX CP logs.
- `CPLEX/MIP/results/preprocessing/` and `CPLEX/MIP/results/no_preprocessing/` contain the CPLEX MIP logs.
- `CPSAT/results/preprocessing/` and `CPSAT/results/no_preprocessing/` contain the CPSAT logs.
- `SAT/DSE/results/preprocessing/` and `SAT/DSE/results/no_preprocessing/` contain the SAT DSE logs.
- `SAT/POSE/results/preprocessing/INC/`, `SAT/POSE/results/no_preprocessing/INC/`, `SAT/POSE/results/preprocessing/INCSC/`, and `SAT/POSE/results/no_preprocessing/INCSC/` contain the SAT POSE logs.
- `EvalMaxSAT/results/processing/pipeline/` and `EvalMaxSAT/results/no_preprocessing/pipeline/` contain the EvalMaxSAT logs.
- `MaxSAT-RC2/results/processing/` and `MaxSAT-RC2/results/no_processing/` contain the MaxSAT-RC2 logs.

## Common Issues

1. `ModuleNotFoundError: gurobipy`
Install the Gurobi Python package and confirm that your Gurobi license is active.

2. `ModuleNotFoundError: cplex` or CP Optimizer errors
Install IBM CPLEX Optimization Studio and the matching Python bindings.

3. Permission denied on `runlim` or shell scripts
Run the executable-bit commands in the installation section.

4. SAT solver name not available
Use a solver supported by your PySAT installation, such as `cadical195` or `glucose4`.

