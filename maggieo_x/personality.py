from enum import Enum
from typing import Optional
import purepyindi2
from dataclasses import dataclass
import xml.etree.ElementTree as ET

class Operation(Enum):
    eq = 'eq'
    lt = 'lt'
    le = 'le'
    gt = 'gt'
    ge = 'ge'
    ne = 'ne'
    def __str__(self):
        return self.value

@dataclass(eq=True, frozen=True)
class Transition:
    value : Optional[purepyindi2.AnyIndiValue]
    op : Optional[Operation] = None

    def compare(self, new_value):
        if self.op is None:
            return True
        if self.op is Operation.EQ:
            return new_value == self.value
        elif self.op is Operation.NE:
            return new_value != self.value
        elif self.op is Operation.LT:
            return new_value < self.value
        elif self.op is Operation.LE:
            return new_value <= self.value
        elif self.op is Operation.GT:
            return new_value > self.value
        elif self.op is Operation.GE:
            return new_value >= self.value
        return False

@dataclass
class Reaction:
    indi_id : str
    transitions : dict[Transition, list[str]]

@dataclass
class Personality:
    reactions : list[Reaction]
    default_voice : str
    
    @classmethod
    def from_path(cls, file_path):
        tree = ET.parse(file_path)
        root = tree.getroot()
        reactions = []
        default_voice = None

        for el in root:
            transitions = {}
            if el.tag == 'default-voice':
                default_voice = el.attrib['name']
                continue
            assert el.tag == 'react-to'
            indi_id = el.attrib['indi-id']
            for transition in el:
                assert transition.tag == 'transition'
                if 'value' in transition.attrib:
                    value = purepyindi2.parse_string_into_any_indi_value(transition.attrib['value'])
                    operation = purepyindi2.parse_string_into_enum(transition.attrib.get('op', 'eq'), Operation)
                else:
                    value = None
                    operation = None
                trans = Transition(op=operation, value=value)
                if trans in transitions:
                    raise RuntimeError(f"Multiply defined for {indi_id} {operation=} {value=}")
                transitions[trans] = []
                for utterance in transition:
                    assert utterance.tag == 'speak'
                    transitions[trans].append(ET.tostring(utterance, 'utf-8').decode('utf8').strip())
            reactions.append(Reaction(indi_id=indi_id, transitions=transitions))
        return cls(reactions=reactions, default_voice=default_voice)

if __name__ == "__main__":
    import pprint
    pprint.pprint(Personality.from_path('./default.xml'), width=255)