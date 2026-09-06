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

or

```
python ./src/part1/main.py
```

### Part 2

The CLI command to execute this module is as follow:


```
python -m src.part2.main
```

or

```
python ./src/part2/main.py
```

#### Arguments:

```txt
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
                        If `mode` is set to 'train' and `device` is a CPU type, sets the number of parallel training processes (limited by the number of available CPU cores). Default: 1.
  -d {auto,cpu,cuda,ipu,xpu,mkldnn,opengl,opencl,ideep,hip,ve,fpga,maia,xla,lazy,vulkan,mps,meta,hpu,mtia,privateuseone}, --device {auto,cpu,cuda,ipu,xpu,mkldnn,opengl,opencl,ideep,hip,ve,fpga,ma}
                        If `mode` is set to 'train', sets the device used by the training algorithm. Default: 'auto'.
  -M MODEL_PATH, --model-path MODEL_PATH
                        If `mode` is set to 'train' or 'evaluate', sets path to the output/input model. If `mode` is 'train' and this is not specified, a default path in 'models/part2' will be
                        used.
  -p START_PHASE, --start-phase START_PHASE
                        If `mode` is set to 'play' or 'evaluate', starts the game at the specified phase. Default: 0.
  -v VERBOSE, --verbose VERBOSE
                        Sets the CLI output verbose level. Default: 0.
```

For more information, please use the `-h`, `-help`, or `--help` flag.

#### Configuration files:

- `src/part2/game_phases.json`: Contains the layout and data for all game phases of this module.
- `src/part2/rl_env_hparams.json`: Contains the hyperparameters for the RL game environment of this module, including agent sensor capability and reward function tunings.
- `src/part2/rl_model_hparams.json`: Contains the hyperparameters for RL algorithms available in this module.
- `src/part2/rl_train_hparams.json`: Contains the hyperparameters for the RL training procedure of this module.


### Outputs:

- `models/part2`: Default trained model export directory.
- `logs/part2`: Training logs directory (Tensorboard and CSV). Use `tensorboard --logdir /logs/part2` to view.
