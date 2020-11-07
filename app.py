import sys 
from intcode import IntCodeCpu
from itertools import combinations

def d(output_buffer):
    print("".join([ chr(c) for c in output_buffer]))
    return len(output_buffer) == 0

# some shortcuts I used when exploring
def parse_cmd(cmd):
    if cmd == "w":
        return "north"
    if cmd == "s":
        return "south"
    if cmd == "d":
        return "east"
    if cmd == "a":
        return "west"
    return cmd

def get_command():
    if len(buffered_instructions) > 0:
        return buffered_instructions.pop(0).strip()
    return input(prompt)

def c(cmd=None):
    global cpu
    output_buffer = []

    if cmd:
        cmd = parse_cmd(cmd)
        cmd = [ord(c) for c in f"{cmd}\n"][::-1]
        cpu.start(cmd, output_buffer)
    else:
        cpu.start([], output_buffer)
    
    return d(output_buffer)

all_items = [ "manifold","dehydrated water","polygon","weather machine","bowl of rice","hypercube","candy cane","dark matter"]

def item_combinations():
    # possible items that don't kill me, send me into space, get me stuck or send me into an infinite loop
    for subset_length in range(len(all_items) + 1):
        for subset in combinations(all_items, subset_length):
            yield subset

def cycle_through_item_combos():
    # start off by dropping everything 
    item_instructions = [ f"drop {item}" for item in all_items ]

    # next we'll iterate over all combinations and:
    # 1. 'take' everything in the combination
    # 2. move south
    # 3. drop what we have
    for item_combo in item_combinations():
        item_instructions += [ f"take {item}" for item in item_combo ]
        item_instructions.append("south")
        item_instructions += [ f"drop {item}" for item in item_combo ]

    return item_instructions

buffered_instructions = open("./retrieve-all-items.txt").readlines() + cycle_through_item_combos()

code = open("./puzzle-input.txt").read().split(",")
cpu = IntCodeCpu(code)
prompt = "> "
command = None
done = False
while command != "q" and not done:
    done = c(command)
    command = get_command()