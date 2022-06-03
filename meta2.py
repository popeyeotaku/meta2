"""MetaII assembly VM"""

from __future__ import annotations
import re
from sys import argv
from dataclasses import dataclass, field
from string import whitespace
from typing import Callable, Union


class MetaSyntax(Exception):
    """A META-II syntax error -- a VM halt."""


@dataclass(eq=False)
class VM:
    """The Meta-II VM."""
    program_counter: int
    memory: list[tuple[Callable[[VM, tuple], None], tuple]]
    switch: bool = field(default=False, init=False)
    inbuf: str = field(default='')
    outbuf: str = field(default='', init=False)
    outline: str = field(default='', init=False)
    outlabel: bool = field(default=False, init=False)
    labels: dict[str, int] = field(default_factory=dict)
    stack: list = field(default_factory=list, init=False)
    inbuf_index: int = field(default=0)
    deleted: str = field(default='', init=False)
    templabel: int = field(default=0, init=False)

    def reset(self) -> None:
        """Reset internal state."""
        self.stack = []
        self.outbuf = ''
        self.outlabel = False
        self.outline = ''
        self.deleted = ''
        self.switch = False
        self.templabel = 0

    @property
    def input(self) -> str:
        """Return out input buffer from the current index only."""
        return self.inbuf[self.inbuf_index:]

    def seek(self, i: int, relative: bool = True) -> None:
        """Seek our input index."""
        if relative:
            i += self.inbuf_index
        self.inbuf_index = max(0, i)

    def skip_ws(self) -> None:
        """Skip leading whitespace."""
        while len(self.input) > 0 and self.input[0] in whitespace:
            self.seek(1)

    def delete(self, chars: int) -> None:
        """Delete up to chars characters from our input string, storing them
        in self.deleted.
        """
        self.deleted = self.input[:chars]
        self.seek(chars)

    @property
    def linenum(self) -> int:
        """Return the current input line number."""
        return self.inbuf[:self.inbuf_index].count('\n') + 1

    def resolve(self, elem: Union[str, int]) -> int:
        """Resolve a target to either an already-numeric address, or an
        internal label name's address.
        """
        if isinstance(elem, str):
            return self.labels[elem]
        return elem


def newop(opcodes: dict[str, Callable[[VM, tuple], None]], name: str):
    """Decorator to build an opcode."""
    def inner(func: Callable):
        opcodes[name] = func
    return inner


metaops = {}  # type:dict[str, Callable[[VM, tuple], None]]


@newop(metaops, 'tst')
def op_tst(meta_vm: VM, args) -> None:
    """Skipping leading whitespace, if the input buffer matches the arg
    string, set the switch and skip it in the input. Else, reset the switch.
    """
    meta_vm.skip_ws()
    if meta_vm.input.startswith(args[0]):
        meta_vm.delete(len(args[0]))
        meta_vm.switch = True
    else:
        meta_vm.switch = False


@newop(metaops, 'id')
def op_id(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """After skipping leading whitespace, if we see an identifier, delete it
    and set the switch. Else, reset the switch.
    """
    meta_vm.skip_ws()
    match = re.match(r'[a-zA-Z][a-zA-Z0-9]*', meta_vm.input)
    if match is not None:
        meta_vm.delete(len(match[0]))
        meta_vm.switch = True
    else:
        meta_vm.switch = False


@newop(metaops, 'num')
def op_num(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """Skipping leading whitespace, if the input buffer starts with a number,
    set the switch and delete it. Else, reset the switch.
    """
    meta_vm.skip_ws()
    match = re.match(r'[0-9]+(\.[0-9]+)*', meta_vm.input)
    if match is not None:
        meta_vm.delete(len(match[0]))
        meta_vm.switch = True
    else:
        meta_vm.switch = False


@newop(metaops, 'sr')
def op_sr(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """Skipping leading whitespace, if we see a string, delete it and set the
    switch. Else, reset the switch.
    """
    meta_vm.skip_ws()
    match = re.match(r"'[^']+'", meta_vm.input)
    if match is not None:
        meta_vm.delete(len(match[0]))
        meta_vm.switch = True
    else:
        meta_vm.switch = False


@newop(metaops, 'cll')
def op_cll(meta_vm: VM, args) -> None:
    """Call the given label."""
    if len(meta_vm.stack) >= 2 and meta_vm.stack[-2:] == [0, 0]:
        meta_vm.stack.append(0)
        flag = -1
    else:
        meta_vm.stack += [0, 0, 0]
        flag = 1
    meta_vm.stack[-3] = meta_vm.program_counter * flag
    meta_vm.program_counter = meta_vm.resolve(args[0])


@newop(metaops, 'r')
def op_r(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """Execute a return."""
    retaddr = meta_vm.stack[-3]
    if retaddr < 0:
        retaddr = -retaddr
        meta_vm.stack.pop()
        meta_vm.stack[-2:] = [0, 0]
    else:
        del meta_vm.stack[-3:]
    meta_vm.program_counter = retaddr


@newop(metaops, 'set')
def op_set(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """Set the branch switch."""
    meta_vm.switch = True


@newop(metaops, 'b')
def op_b(meta_vm: VM, args) -> None:
    """Branch unconditionally."""
    meta_vm.program_counter = meta_vm.resolve(args[0])


@newop(metaops, 'bt')
def op_bt(meta_vm: VM, args) -> None:
    """Branch if switch set."""
    if meta_vm.switch:
        meta_vm.program_counter = meta_vm.resolve(args[0])


@newop(metaops, 'bf')
def op_bf(meta_vm: VM, args) -> None:
    """Branch if switch reset."""
    if not meta_vm.switch:
        meta_vm.program_counter = meta_vm.resolve(args[0])


@newop(metaops, 'be')
def op_be(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """If the switch if reset halt."""
    if not meta_vm.switch:
        raise MetaSyntax


@newop(metaops, 'cl')
def op_cl(meta_vm: VM, args) -> None:
    """Copy the inline arg to the output."""
    meta_vm.outline += args[0]


@newop(metaops, 'ci')
def op_ci(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """Copy the deleted text to the output."""
    meta_vm.outline += meta_vm.deleted


def op_gn(meta_vm: VM, offset: int) -> None:
    """Generate the given temp label (offset 1 or 2) if needbe, and output
    it.
    """
    label = meta_vm.stack[-offset]
    if label == 0:
        meta_vm.templabel += 1
        label = meta_vm.templabel
        meta_vm.stack[-offset] = label
    meta_vm.outline += f"l{label}"


@newop(metaops, 'gn1')
def op_gn1(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """Output/generate label 1."""
    op_gn(meta_vm, 1)


@newop(metaops, 'gn2')
def op_gn2(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """Output/generate label 2."""
    op_gn(meta_vm, 2)


@newop(metaops, 'lb')
def op_lb(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """Set the flag so that the current line will start with a label."""
    meta_vm.outlabel = True


@newop(metaops, 'out')
def op_out(meta_vm: VM, args) -> None:  # pylint:disable=unused-argument
    """Output the current line and reset outlabel."""
    if not meta_vm.outlabel:
        meta_vm.outbuf += '\t'
    meta_vm.outbuf += meta_vm.outline + '\n'
    meta_vm.outlabel = False
    meta_vm.outline = ''


class MetaII:
    """The MetaII VM exceutor."""

    def __init__(self):
        self.meta_vm = VM(0, [])
        self.opcodes = metaops
        self.start = 0

    def assemble(self, assembly: str) -> None:
        """Assemble the given source code, storing it in the VM."""
        labels = {}  # type:dict[str, int]
        memory = []
        start = 0
        for line in assembly.splitlines():
            if all(map(lambda c: c in whitespace, line)):
                continue
            if line[0] not in whitespace:
                labels[line.lstrip().rstrip()] = len(memory)
                continue
            split = map(lambda s: s.lstrip().rstrip(), line.split(maxsplit=1))
            opcode = next(split)
            args = []
            for arg in split:
                match = re.match(r"'([^']+)'", arg)
                if match:
                    args.append(match[1])
                    continue
                match = re.match(r'[0-9]+', arg)
                if match:
                    args.append(int(arg))
                    continue
                args.append(arg)
            if opcode in self.opcodes:
                memory.append((self.opcodes[opcode], tuple(args)))
            elif opcode == 'adr':
                start = args[0]
            elif opcode == 'end':
                break
            else:
                raise ValueError(f"bad opcode {opcode} in line {repr(line)}")
        self.meta_vm.memory = memory
        self.meta_vm.labels = labels
        self.start = self.meta_vm.resolve(start)

    def step(self) -> None:
        """Run a single step of the VM."""
        opcode, args = self.meta_vm.memory[self.meta_vm.program_counter]
        self.meta_vm.program_counter += 1
        opcode(self.meta_vm, args)

    def run(self, source: str) -> Union[str, None]:
        """Run the source code."""
        self.meta_vm.reset()
        self.meta_vm.inbuf = source
        self.meta_vm.program_counter = self.start
        self.meta_vm.stack += [len(self.meta_vm.memory), 0, 0]
        while self.meta_vm.program_counter < len(self.meta_vm.memory):
            try:
                self.step()
            except MetaSyntax:
                print(f"SYNTAX ERROR IN LINE {self.meta_vm.linenum}")
                return None
        if self.meta_vm.switch:
            return self.meta_vm.outbuf
        print(f"SYNTAX ERROR IN LINE {self.meta_vm.linenum}")
        return None


def test(inp, outp):
    """Test the VM."""
    with open(inp, 'r', encoding='utf8') as src:
        asm = src.read()
    with open('meta2.meta2', 'r', encoding='utf8') as src:
        meta2 = src.read()
    meta = MetaII()
    meta.assemble(asm)
    result = meta.run(meta2)
    if result is not None:
        with open(outp, 'w', encoding='utf8') as dest:
            dest.write(result)


if __name__ == "__main__":
    test(argv[1], argv[2])
