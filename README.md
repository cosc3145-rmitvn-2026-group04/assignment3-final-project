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
│   ├── 📂common/       # Source code - Common classes and utilities
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
usage: main.py [-h] -m {train,evaluate,play} [-M MODEL_PATH] [-p START_PHASE]

Assignment 3 [Undergrad] - Part 2: Arena Deep RL

options:
  -h, --help            show this help message and exit
  -m {train,evaluate,play}, --mode {train,evaluate,play}
                        Train without graphics, evaluate the learned policy (agent playing the game), or manually play the game.
  -M MODEL_PATH, --model-path MODEL_PATH
                        If `mode` is set to `train` or `evaluate`, overrides path to the output/input model.
  -p START_PHASE, --start-phase START_PHASE
                        If `mode` is set to `play`, start the game at the specified phase.
```

For more information, please use the `-h`, `-help`, or `--help` flag.
