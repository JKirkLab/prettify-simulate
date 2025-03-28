from opentrons.simulate import simulate, format_runlog
import io
import re

from contextlib import redirect_stdout
from rich.console import Console
from rich.text import Text
from rich.panel import Panel


protocol_file = open("../RobotProtocols/Protocols/Peptide_Quant_Assay.py")
runlog, _bundle = simulate(
    protocol_file,
    custom_labware_paths=["../RobotProtocols/"] 
)
output_stream = io.StringIO()
with redirect_stdout(output_stream):
    print(format_runlog(runlog))
runlog_output = output_stream.getvalue()
steps = runlog_output.strip().splitlines()

action_patterns = {
    "Aspirating": (
        r"^Aspirating.*",
        r"^Aspirating (?P<amount>\d+\.?\d*) uL from "
        r"(?P<well>[A-Z]\d{1,2}) of "
        r"(?P<labware>.+?) on slot "
        r"(?P<slot>[A-Z]\d) at "
        r"(?P<speed>\d+\.?\d* uL/sec)"
    ),
    "Dispensing": (
        r"^Dispensing.*",
        r"^Dispensing (?P<amount>\d+\.?\d*) uL into "
        r"(?P<well>[A-Z]\d{1,2}) of "
        r"(?P<labware>.+?) on slot "
        r"(?P<slot>[A-Z]\d) at "
        r"(?P<speed>\d+\.?\d* uL/sec)"
    ),
    "Pick up tip": (
        r"^Picking up tip.*",
        r"^Picking up tip from (?P<position>[A-H]\d{1,2}) of "
        r"(?P<labware>.+?) on slot (?P<slot>[A-Z]\d)"
    ),
    "Dropping tip": (
        r"^Dropping tip.*",
        r"^Dropping tip into (?P<labware>.+?)"
        r" on slot (?P<slot>[A-Z]\d)"
    ),
    "Pausing": (
        r"^Pausing robot operation:.*",
        r"^Pausing robot operation: (?P<message>.+)"
    ),
    "Mixing": (
        r"^Mixing .*",
        r"^Mixing (?P<number>\d+) times with a volume of (?P<volume>\d+\.?\d*) ul"
    )
}

def parse_step(step: str) -> dict | None:
    for action, (match_pattern, extract_pattern) in action_patterns.items():
        if re.match(match_pattern, step):
            match = re.match(extract_pattern, step)
            if match:
                return {"action": action, **match.groupdict()}
    return None


unmatched = []
parsed_actions = []
for step in steps:
    parsed = parse_step(step)
    if parsed == None:
        unmatched.append(step)
        pass
    else:
        parsed_actions.append(parsed)
print(f"\nParsed: {len(steps) - len(unmatched)}")
print(f"Unmatched: {len(unmatched)}\n")

for step in unmatched:
    print(f"{step}")
# for step in parsed_actions:
#     print(step)
source_labware = None
destination_labware = None

current_group = []
grouped_steps = []

pickup_buffer = None
aspirate_buffer = None

for action in parsed_actions:
    action_type = action["action"]

    new_source = False
    new_dest = False

    if action_type == "Pausing":
        if current_group:
            grouped_steps.append(current_group)
            current_group = []
        grouped_steps.append([action])
        continue

    if action_type == "Pick up tip":
        pickup_buffer = action
        continue

    if action_type == "Aspirating":
        asp_id = action['labware'] + " " + action['slot']
        if asp_id!= source_labware and source_labware is not None:
            new_source = True
        source_labware = asp_id

        if new_source:
            if current_group:
                grouped_steps.append(current_group)
            current_group = []
        
            if pickup_buffer:
                current_group.append(pickup_buffer)
                pickup_buffer = None
        
        aspirate_buffer = action
        continue
        
            
    if action_type == "Dispensing":
        disp_id = action['labware'] + " " + action['slot']
        if disp_id != destination_labware and destination_labware is not None:
            new_dest = True
        destination_labware = disp_id

        if new_dest:
            if current_group:
                grouped_steps.append(current_group)
            current_group = []
        
        if pickup_buffer:
            current_group.append(pickup_buffer)
            pickup_buffer = None
        if aspirate_buffer:
            current_group.append(aspirate_buffer)
            aspirate_buffer = None

        current_group.append(action)
        continue

    current_group.append(action)

if current_group:
    grouped_steps.append(current_group)
console = Console()

def summarize(groups: list[list[dict]]):
    for i, group in enumerate(groups):
        source_info = None
        dest_info = None
        transfers = []
        tips_used = 0
        mix_summary = set()
        pauses = []

        amount = None
        source_well = None

        for step in group:
            action = step["action"]

            if action == "Pick up tip":
                tips_used += 1

            elif action == "Aspirating":
                source_info = f"{step['labware']} @ {step['slot']}"
                source_well = step["well"]

            elif action == "Dispensing":
                dest_info = f"{step['labware']} @ {step['slot']}"
                dest_well = step["well"]
                dispense_amount = step["amount"]
                if dispense_amount and source_well:
                    transfers.append((dispense_amount, source_well, dest_well))

            elif action == "Mixing":
                mix_summary.add(f"{step['number']}x @ {step['volume']} µL")

            elif action == "Pausing":
                pauses.append(step['message'])

        if source_info and dest_info:
            header = Text(f"[{i+1}] {source_info} → {dest_info}", style="bold")
            body = Text()

            for amt, src, dst in transfers:
                body.append(f"{amt}", style="cyan")
                body.append(" µL ")
                body.append(f"{src}", style="green")
                body.append(" → ")
                body.append(f"{dst}\n", style="magenta")

            if mix_summary:
                body.append("\n")
                for mix in mix_summary:
                    body.append(f"Mix {mix}\n", style="blue")

            if tips_used:
                body.append(f"\nTips used: {tips_used}", style="bold magenta")

            panel = Panel(body, title=header, border_style="green", expand=False)
            console.print(panel)
        else:
            step = group[0]
            if step["action"] == "Pausing":
                pause_text = Text(f"Pause: {step['message']}", style="yellow")
                panel = Panel(pause_text, title=f"[{i+1}] Pause", border_style="orange3", expand=False)
                console.print(panel)

summarize(grouped_steps)