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
