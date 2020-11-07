opcode_add = 1
opcode_mul = 2
opcode_read = 3
opcode_write = 4
opcode_jump_true = 5
opcode_jump_false = 6
opcode_lt = 7
opcode_eq = 8
opcode_rebase = 9

opcode_terminate = 99

mode_position = 0
mode_immediate = 1
mode_relative = 2

class IntCodeCpu:
    def __init__(self, memory_image):
        self.memory = [ x for x in memory_image ] # copy memory image, in case it's reused
        self.stalled = True
        self.input_buffer = None
        self.output_buffer = None
        self.pc = 0
        self.initialise_opcodes()
        self.offset = 0
        self.done = False
        
    def start(self, input_buffer, output_buffer, noun=None, verb=None):
        self.input_buffer = input_buffer
        self.output_buffer = output_buffer

        if noun:
            self.memory[1] = noun
        if verb:
            self.memory[2] = verb
           
        return self.run()
            
            
    def run(self):
        instr = self.memory[self.pc]
        self.stalled = False

        while int(instr) != opcode_terminate and not self.stalled:
            (op, modes) = self.decode_instr(instr)
            self.pc = op(modes)
            instr = self.memory[self.pc]

        return self.memory[0]

    #-HELPERS-----------------------------
    def try_pop_mode(self, modes):
        if len(modes) == 0:
            return 0
    
        return modes.pop()
    
    def resize_memory(self, target_addr):
        self.memory += ([0] * (1 + target_addr - len(self.memory)))
    
    #-DECODE-INSTRUCTIONS-----------------
    def initialise_opcodes(self):
        self.opcodes = {
            opcode_add: self.op_add,
            opcode_mul: self.op_mul,
            opcode_read: self.op_read,
            opcode_write: self.op_write,
            opcode_jump_true: self.op_jump_true,
            opcode_jump_false: self.op_jump_false,
            opcode_lt: self.op_lt,
            opcode_eq: self.op_eq,
            opcode_rebase: self.op_rebase
        }    
    
    def decode_instr(self, instr):
        instr = str(instr)
        opcode = self.decode_op(instr)
        modes = self.decode_modes(instr)

        if not (opcode in self.opcodes):
            raise Exception(f"Invalid opcode {opcode}")

        return (self.opcodes[opcode], modes)    
    
    def decode_op(self, instr):
        if len(instr) > 2:
            return int(instr[-2:])
        return int(instr)
    
    def decode_modes(self, instr):
        if len(instr) > 2:
            return [ int(d) for d in instr[:-2]]
        return []
    
    #-MICRO-OPS---------------------------
    def uop_read(self, value, mode):
        if mode == mode_position:
            if value >= len(self.memory):
                self.resize_memory(value)        

            return int(self.memory[value])

        elif mode == mode_relative:
            if self.offset + value >= len(self.memory):
                self.resize_memory(self.offset + value)     

            return int(self.memory[self.offset + value])

        elif mode == mode_immediate:
            return int(value)

        else:
            raise Exception("UNKNOWN MODE")

    def uop_write(self, dst, value, mode):
        if mode == mode_position:
            if dst >= len(self.memory):
                self.resize_memory(dst)
            self.memory[dst] = value

        elif mode == mode_relative:
            if self.offset + dst >= len(self.memory):
                self.resize_memory(self.offset + dst)     

            self.memory[self.offset + dst] = value

        elif mode == mode_immediate:
            raise Exception(f"cannot write {value} to literal {dst}")


    def uop_cond_jump(self, modes, cond):
        param_mode = self.try_pop_mode(modes)
        param_raw = int(self.memory[self.pc + 1])
        param = self.uop_read(param_raw, param_mode)

        dest_mode = self.try_pop_mode(modes)
        dest_raw = int(self.memory[self.pc + 2])
        dest = self.uop_read(dest_raw, dest_mode)

        if cond(param):
            return dest

        return self.pc + 3

    def uop_cmp(self, modes, cmp):

        param0_mode = self.try_pop_mode(modes)
        param0_raw = int(self.memory[self.pc + 1])
        param0 = self.uop_read(param0_raw, param0_mode)

        param1_mode = self.try_pop_mode(modes)
        param1_raw = int(self.memory[self.pc + 2])
        param1 = self.uop_read(param1_raw, param1_mode)

        dest_mode = self.try_pop_mode(modes)
        dest = int(self.memory[self.pc + 3])

        if cmp(param0, param1):
            self.uop_write(dest, 1, dest_mode)
        else:
            self.uop_write(dest, 0, dest_mode)

        return self.pc + 4
        
    
    #-OPCODES-----------------------------
    def op_add(self, modes):
        arg0_mode = self.try_pop_mode(modes)
        arg1_mode = self.try_pop_mode(modes)
        dest_mode = self.try_pop_mode(modes)

        arg0_raw = int(self.memory[self.pc + 1])
        arg1_raw = int(self.memory[self.pc + 2])
        dest = int(self.memory[self.pc + 3])

        arg0 = self.uop_read(arg0_raw, arg0_mode)
        arg1 = self.uop_read(arg1_raw, arg1_mode)

        self.uop_write(dest, str(int(arg0) + int(arg1)), dest_mode)
        return self.pc + 4

    def op_mul(self, modes):
        arg0_mode = self.try_pop_mode(modes)
        arg1_mode = self.try_pop_mode(modes)
        dest_mode = self.try_pop_mode(modes)

        arg0_raw = int(self.memory[self.pc + 1])
        arg1_raw = int(self.memory[self.pc + 2])
        dest = int(self.memory[self.pc + 3])

        arg0 = self.uop_read(arg0_raw, arg0_mode)
        arg1 = self.uop_read(arg1_raw, arg1_mode)

        self.uop_write(dest, str(int(arg0) * int(arg1)), dest_mode)    
        return self.pc + 4


    def op_read(self, modes):
        dest_mode = self.try_pop_mode(modes)
        dest = int(self.memory[self.pc + 1])
        
        # if the input buffer is empty, we should "stall" and 
        # resume later
        if not self.input_buffer:
            self.stalled = True
            return self.pc
        
        val = self.input_buffer.pop()

        self.uop_write(dest, str(val), dest_mode)

        return self.pc + 2

    def op_write(self, modes):
        src_mode = self.try_pop_mode(modes)
        src_raw = int(self.memory[self.pc + 1])
        src = self.uop_read(src_raw, src_mode)

        self.output_buffer.append(src)

        return self.pc + 2

    def op_jump_true(self, modes):
        return self.uop_cond_jump(modes, lambda x: x != 0)


    def op_jump_false(self, modes):
        return self.uop_cond_jump(modes, lambda x: x == 0)

    def op_lt(self, modes):
        return self.uop_cmp(modes, lambda x, y: x < y)

    def op_eq(self, modes):
        return self.uop_cmp(modes, lambda x, y: x == y)

    def op_rebase(self, modes):    
        param_mode = self.try_pop_mode(modes)
        param_raw = int(self.memory[self.pc + 1])
        param = self.uop_read(param_raw, param_mode)

        self.offset += param

        return self.pc + 2