#!/usr/bin/env python3
# coding=utf-8
from functools import partial
from itertools import zip_longest
from operator import is_not
from sys import stderr
from typing import Optional, Iterable

FILE_PATTERN = """architecture behavioral of fsm is
    type t_state is (
        {states_enum},

        {wrong_state},
        {print_fail},
        {print_success},
        {finish_state_name}
    );
    signal {current_state_name}, {next_state_name} : t_state;
begin
-- -------------------------------------------------------
next_state_logic : process({current_state_name}, KEY, CNT_OF)
begin
   case ({current_state_name}) is
   {code_states}

    when {wrong_state} =>
        {next_state_name} <= {wrong_state};
        if KEY(15) = '1' then
            {next_state_name} <= {print_fail};
        end if;
    when {print_success} =>
        {next_state_name} <= {print_success};
        if (CNT_OF = '1') then
            {next_state_name} <= {finish_state_name};
        end if;
    when {print_fail} =>
        {next_state_name} <= {print_fail};
        if (CNT_OF = '1') then
            {next_state_name} <= {finish_state_name};
        end if;
    when {finish_state_name} =>
        {next_state_name} <= {finish_state_name};
        if KEY(15) = '1' then
            {next_state_name} <= {first_code_state};
        end if;
    when others =>
        {next_state_name} <= {first_code_state};
   end case;
end process next_state_logic;

-- TODO sync logic
-- TODO output logic

end architecture behavioral;
"""


class Config(object):
    """
    Holds loaded generator configuration.
    """

    code1 = code2 = ""
    next_state_name = 'next_state'
    present_state_name = 'present_state'
    code_state_pattern = 'test_{}'
    finish_state_name = 'finish'
    wrong_code_state = 'wrong_code_state'
    print_success_state = "print_success"
    print_fail_state = 'print_fail'
    output_file = 'output.vhd'

    @classmethod
    def load(cls):
        conf = Config()
        conf.next_state_name = input("Next state signal name [next_state]: ").strip() or cls.next_state_name
        conf.present_state_name = input("Present state signal name [present_state]: ").strip() or cls.present_state_name
        conf.code_state_pattern = input("Code state pattern [test_{}]: ").strip() or cls.code_state_pattern

        conf.wrong_code_state = input("Wrong code state name [wrong_code]: ").strip() or cls.wrong_code_state
        conf.print_success_state = input("State to print success [print_success]: ").strip() or cls.print_success_state
        conf.print_fail_state = input("State to print success [print_fail]: ").strip() or cls.print_fail_state
        conf.finish_state_name = input("State to finish [finish]: ").strip() or cls.finish_state_name
        conf.output_file = input("File to write [output.vhd]: ").strip() or cls.output_file

        conf.code1 = input("Code 1: ").strip()
        conf.code2 = input("Code 2: ").strip()

        if not conf.code1 or not conf.code2 or not conf.code1.isdigit() or not conf.code2.isdigit():
            return None

        return conf


class State(object):
    """
    Holds one case of FSM switch with info to get to next state (or success/fail print).
    """
    _NEXT_STATE_BRANCH = """
        if (KEY({key}) = '1') then
            {next_state_name} <= {next_state};
        end if;"""

    PATTERN = """
    when {current_state} =>
        {next_state_name} <= {current_state};
        if KEY(15) = '1' then
            {next_state_name} <= {print_fail};
        elsif KEY(15 downto 0) /= "0000000000000000" then
            {next_state_name} <= {wrong_code_state};
        {next_state_branch}
        end if;"""
    PATTERN_LAST_STATE = """
    when {current_state} =>
        {next_state_name} <= {current_state};
        if KEY(15) = '1' then
            {next_state_name} <= {print_success};
        elsif KEY(15 downto 0) /= "0000000000000000" then
            {next_state_name} <= {wrong_code_state};
        end if;"""

    def __init__(self, next_state_key: Optional[str], char_index: int,
                 config: Config, code_index: int, splitter: Optional[Iterable[str]] = None, is_last: bool = False):
        self.next_state_key = next_state_key
        self.char_index = char_index
        self.config = config
        self.code_index = code_index
        self.splitter = splitter
        self.is_last = is_last

    @classmethod
    def state_name(cls, config: Config, code_index: int, symbol_index: int):
        return config.code_state_pattern.format('_'.join(map(str, filter(partial(is_not, None), (
            symbol_index,
            code_index
        )))))

    @property
    def current_state(self):
        return self.state_name(self.config, self.code_index, self.char_index)

    @property
    def next_state(self):
        return self.state_name(self.config, self.code_index, self.char_index + 1)

    @property
    def vhdl(self):
        if self.splitter is not None:
            return self.PATTERN.format(
                current_state=self.current_state,
                current_state_name=self.config.present_state_name,
                next_state=self.next_state,
                wrong_code_state=self.config.wrong_code_state,
                print_fail=self.config.print_fail_state if not self.is_last else self.config.print_success_state,
                next_state_name=self.config.next_state_name,
                next_state_branch='\n'.join(self._NEXT_STATE_BRANCH.format(
                    key=next_state_key,
                    next_state_name=self.config.next_state_name,
                    next_state=self.state_name(config, index, self.char_index + 1)
                ) for index, next_state_key in enumerate(self.splitter, 1))
            )
        elif not self.is_last:
            return self.PATTERN.format(
                current_state=self.current_state,
                current_state_name=self.config.present_state_name,
                next_state=self.next_state,
                wrong_code_state=self.config.wrong_code_state,
                print_fail=self.config.print_fail_state,
                next_state_name=self.config.next_state_name,
                next_state_branch=self._NEXT_STATE_BRANCH.format(
                    key=self.next_state_key,
                    next_state_name=self.config.next_state_name,
                    next_state=self.next_state
                )
            )

        return self.PATTERN_LAST_STATE.format(
            current_state=self.current_state,
            current_state_name=self.config.present_state_name,
            wrong_code_state=self.config.wrong_code_state,
            print_success=self.config.print_success_state,
            next_state_name=self.config.next_state_name,
        )


def generate(config: Config):
    states = []
    split = False
    code1_len, code2_len = len(config.code1), len(config.code2)
    for i, (num1, num2) in tuple(enumerate(zip_longest(config.code1, config.code2))):
        # is_next_same = config.code1[i + 1: i + 2] == config.code2[i + 1: i + 2]
        if not split:
            if num1 == num2:  # shared state
                state = State(
                    next_state_key=num1,
                    char_index=i,
                    config=config,
                    code_index=0,
                    is_last=code1_len - 1 == i
                )
            else:
                state = State(
                    next_state_key=None,
                    char_index=i,
                    config=config,
                    code_index=0,
                    splitter=(
                        num1,
                        num2,
                    ),
                    is_last=code1_len - 1 == i
                )
                split = True
            states.append(state)
            continue

        if num1:
            states.append(State(
                next_state_key=num1,
                char_index=i,
                config=config,
                code_index=1,
                is_last=code1_len == i
            ))
        if num2:
            states.append(State(
                next_state_key=num2,
                char_index=i,
                config=config,
                code_index=2,
                is_last=code2_len == i
            ))

    states.append(State(
        next_state_key=None,
        char_index=code1_len,
        config=config,
        code_index=1,
        is_last=True
    ))
    states.append(State(
        next_state_key=None,
        char_index=code2_len,
        config=config,
        code_index=2,
        is_last=True
    ))

    return FILE_PATTERN.format(
        code_states='\n'.join(state.vhdl for state in states),
        states_enum=', \n\t'.join(state.current_state for state in states),
        wrong_state=config.wrong_code_state,
        print_success=config.print_success_state,
        print_fail=config.print_fail_state,
        next_state_name=config.next_state_name,
        current_state_name=config.present_state_name,
        finish_state_name=config.finish_state_name,
        first_code_state=State.state_name(config, 0, 0)
    )


if __name__ == '__main__':
    config = Config.load()
    while not config:
        print("Invalid config.", file=stderr)
        config = Config.load()

    """
    config = Config()
    config.code1 = '887653211'
    config.code2 = '8876150458'
    config.output_file = '-'
    """

    generated = generate(config)

    if config.output_file == '-':
        print(generated)
    else:
        with open(config.output_file, 'w') as f:
            f.write(generated)
        print("SUCCESS: Generated states written {}.".format(config.output_file))
