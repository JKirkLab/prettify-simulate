# prettify-simulate

A small module designed to make the output of opentrons simulate more readable. 

The script parses the output of the simulate module opentrons provides natively. It attempts to extract known output patterns, such as Aspirating, Dispensing, Picking up/ Dropping tips etc. Additionally, the program attempts to group actions based on a source to destination criteria. 

The output of the module displays the simplified protocol using Rich. 

## Requirements 

- Python 3.10

## Setup 

### 1. Clone the Repo

```bash
git clone https://github.com/JKirkLab/prettify-simulate.git
cd prettify-simulate
```

### 2. Create the Environment

```bash
python3 -m venv prettify_env
source prettify_env/bin/activate
pip install -r requirements.txt
```
## Usage

```bash
python prettify.py
```

To change which protocol is simulated, edit the file path present at the top of the file as follows: 

```bash
protocol_file = open("ENTER YOUR PATH HERE")
```



