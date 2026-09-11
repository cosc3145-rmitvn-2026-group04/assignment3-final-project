# RMIT2026A - COSC3145 Games and Artificial Intelligence Techniques

Course information: [https://handbook.rmit.edu.au/ords/r/rmit/catalogue/class?p8_code=045680&p8_class_guide_course_of_code=COSC3066&p8_class_guide_class_nbr=1391&p8_class_guide_term_descr=Vietnam%20Semester%202](https://handbook.rmit.edu.au/ords/r/rmit/catalogue/class?p8_code=045680&p8_class_guide_course_of_code=COSC3066&p8_class_guide_class_nbr=1391&p8_class_guide_term_descr=Vietnam%20Semester%202)

---

## Assignment 3 (Undergrad) - Final Project: Reinforcement Learning and DL Agents

Assignment overview: https://rmit.instructure.com/courses/171534/assignments/1247324

## Dependencies

- Python 3.11.
- Other Python packages in `requirements.txt`.

## Structure

```yaml
📂.
├── 📂src/              # Source code
│   ├── 📂part1/        # Source code - Assignment Part 1
│   └── 📂part2/        # Source code - Assignment Part 2
├── .gitignore
├── requirements.txt    # Project dependencies
├── LICENSE             # License information
└── README.md           # This file
```

## Development Setup

### 1. Set up virtual environment (venv)

```powershell
python -m venv venv
git init
```

### 2. Activate virtual environment (venv)

```powershell
.\venv\Scripts\activate
```

To deactivate:

```powershell
deactivate
```

### 3. Install requirements

```powershell
pip install -r requirements.txt
```

## Run

### Part 1

```
python -m src.part1.main
```

#### Arguments:

```txt
usage: main.py [-h] [--level {0,1,2,3,4,5,6}] [--algo {q_learning,sarsa}] [--intrinsic-reward] [--seed SEED] {train,evaluate,manual}

Assignment 3 [Undergrad] - Part 1: Classical RL

positional arguments:
  {train,evaluate,manual}
                        execution mode

options:
  -h, --help            show this help message and exit
  --level {0,1,2,3,4,5,6}
                        gridworld level to run
  --algo {q_learning,sarsa}
                        override the level's default algorithm
  --intrinsic-reward    enable additional intrinsic reward for training
  --seed SEED           override the configured random seed
```

#### Outputs:

- `models/part1`: Trained model export directory.
- `logs/part1`: Training logs directory (.csv files).

### Part 2

```
python -m src.part2.main
```

#### Arguments:

```txt
usage: main.py [-h] -m {train,evaluate,play} [-c {1,2}] [-a {PPO,DQN}] [-s SEED] [-n N_THREADS]
               [-d {auto,cpu,cuda,ipu,xpu,mkldnn,opengl,opencl,ideep,hip,ve,fpga,maia,xla,lazy,vulkan,mps,meta,hpu,mtia,privateuseone}] [-M MODEL_PATH]
               [-P GAME_PHASES] [-p START_PHASE] [-v VERBOSE]

Assignment 3 [Undergrad] - Part 2: Arena Deep RL

options:
  -h, --help            show this help message and exit
  -m {train,evaluate,play}, --mode {train,evaluate,play}
                        Train without graphics, evaluate the learned policy (agent playing the game), or manually play the game.
  -c {1,2}, --control-style {1,2}
                        Sets the control style for 'train' mode. Default: '1'.
  -a {PPO,DQN}, --algorithm {PPO,DQN}
                        Sets the reinforcement learning algorithm for 'train' mode. Default: 'PPO'.
  -s SEED, --seed SEED  If `mode` is set to 'train', sets RNG seed for the training environment. Default: 0.
  -n N_THREADS, --n-threads N_THREADS
                        If `mode` is set to 'train' and `device` is a CPU type, sets the number of parallel training processes (limited by the number of available CPU
                        cores). Default: 1.
  -d {auto,cpu,cuda,ipu,xpu,mkldnn,opengl,opencl,ideep,hip,ve,fpga,maia,xla,lazy,vulkan,mps,meta,hpu,mtia,privateuseone}, --device {auto,cpu,cuda,ipu,xpu,mkldnn,opengl,opencl,ideep,hip,ve,fpga,maia,xla,lazy,vulkan,mps,meta,hpu,mtia,privateuseone}
                        If `mode` is set to 'train', sets the device used by the training algorithm. Default: 'auto'.
  -M MODEL_PATH, --model-path MODEL_PATH
                        If `mode` is set to 'train' or 'evaluate', sets path to the output/input model. If `mode` is 'train' and this is not set, a default path in
                        'models/part2' will be used.
  -P GAME_PHASES, --game-phases GAME_PHASES
                        If `mode` is set to 'play' or 'evaluate', loads the game phases from the specified file path instead of the default in `game_phases.json`.
  -p START_PHASE, --start-phase START_PHASE
                        If `mode` is set to 'play' or 'evaluate', starts the game at the specified phase. Default: 0.
  -v VERBOSE, --verbose VERBOSE
                        Sets the CLI output verbose level. Default: 0.
```

For more information, please use the `-h`, `-help`, or `--help` flag.

#### Examples:

```shell
python -m src.part2.main -v1 -m play  # Play the game manually. CLI Log verbose level 1.
python -m src.part2.main -v2 -m train -a DQN -c1 -n12 -d cpu  # Train a DQN agent for control style 1 using 12 parallel CPU threads. CLI Log verbose level 2.
python -m src.part2.main -v3 -m evaluate -M models/part2/dqn.control_style_1.pkl p2  # Evaluate the model at 'models/part2/dqn.control_style_1.pkl' starting from Phase 2 onward. CLI Log verbose level 3.
python -m src.part2.main -v3 -m evaluate -M models/part2/ppo.control_style_2.pkl -P custom_game_phases.json  # Evaluate the model at 'models/part2/ppo.control_style_2.pkl' using phases loaded from custom_game_phases.json instead of the default game_phases.json. CLI Log verbose level 3.
```

#### Configuration files:

- `src/part2/game_phases.json`: Contains the layout and data for the game phases available in `play` and `evaluate` run modes. `train` mode uses procedurally generated data instead. See `rl_train_hparams.json` below for detail.
- `src/part2/rl_env_hparams.json`: Contains the hyperparameters for the RL game environment of this module, including agent sensor capability and reward function tunings.
- `src/part2/rl_model_hparams.json`: Contains the hyperparameters for RL algorithms available in this module.
- `src/part2/rl_train_hparams.json`: Contains the hyperparameters for the RL training procedure of this module, including configuration for procedural train/test curriculum generation.

#### Outputs:

- `models/part2`: Default trained model export directory.
- `logs/part2/<model_type>.<control_type>.<unix_timestamp>.log`: Training logs directory (TensorBoard output). Use `python -m tensorboard.main --logdir=logs/part2/<model_type>.<control_type>.<unix_timestamp>.log` to view. Replace `<model_type>`, `<control_type>`, and `<unix_timestamp>` with the appropriate values.
