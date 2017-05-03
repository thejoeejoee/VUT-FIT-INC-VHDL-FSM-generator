#!/usr/bin/env python3
# coding=utf-8
from sys import stderr
from typing import Optional, Iterable

FILE_PATTERN = """
architecture behavioral of fsm is
    type t_state is (
        {states_enum}, FINISH
    );
    signal present_state, next_state : t_state;
begin
-- -------------------------------------------------------
next_state_logic : process(present_state, KEY, CNT_OF)
begin
   case (present_state) is
   {code_states}

   when {wrong_state} =>
      -- TODO
   when {print_success} =>
      -- TODO
   when {print_fail} =>
      -- TODO
   when FINISH =>
      -- TODO
   end case;
end process next_state_logic;
end architecture behavioral;
"""


class Config(object):
    """
    Holds loaded generator configuration.
    """

    def __init__(self):
        self.code1 = self.code2 = ""
        self.next_state_name = self.current_state_name = self.code_state_pattern = ""
        self.wrong_code_state = self.print_success_state = self.print_fail_state = ""

    @classmethod
    def load(cls):
        conf = Config()
        conf.next_state_name = input("Next state signal name [next_state]: ").strip() or 'next_state'
        conf.current_state_name = input("Current state signal name [current_state]: ").strip() or 'current_state'
        conf.code_state_pattern = input("Code state pattern [test_{}]: ").strip() or 'test_{}'

        conf.wrong_code_state = input("Wrong code state name [wrong_code]: ").strip() or 'wrong_code_state'
        conf.print_success_state = input("State to print success [print_success]: ").strip() or 'print_success'
        conf.print_fail_state = input("State to print success [print_fail]: ").strip() or 'print_fail'
        conf.output_file = input("File to write [fsm_state.vhd]: ").strip() or 'fsm_state.vhd'

        conf.code1 = input("Code 1: ").strip()
        conf.code2 = input("Code 2: ").strip()

        if not conf.code1 or not conf.code2 or not conf.code1.isdigit() or not conf.code2.isdigit():
            return None

        return conf


class State(object):
    _NEXT_STATE_BRANCH = """
    if (KEY({key}) = '1') then
        {next_state_name} <= {next_state};
    endif;
    """

    PATTERN = """
    when {current_state} =>
        {next_state_name} <= {current_state};
    {next_state_branch}
        if KEY(15) = '1' then
            {next_state_name} <= {print_fail};
        elsif KEY(15 downto 0) /= "0000000000000000" then
            {next_state_name} <= {wrong_code_state};
        end if;
    """
    PATTERN_LAST_STATE = """
    when {current_state} =>
        {next_state_name} <= {current_state};
        if KEY(15) = '1' then
            {next_state_name} <= {print_success};
        elsif KEY(15 downto 0) /= "0000000000000000" then
            {next_state_name} <= {wrong_code_state};
        end if;
    """

    def __init__(self, current_state_number: str, next_state_number: Optional[str],
                 config: Config, code_index: int, splitter: Optional[Iterable[str]] = None):
        self.current = current_state_number
        self.next = next_state_number
        self.config = config
        self.code_index = code_index
        self.splitter = splitter

    @classmethod
    def state_name(cls, config: Config, index: int, symbol: str):
        return config.code_state_pattern.format('_'.join(map(str, filter(None, (
            index,
            symbol
        )))))

    @property
    def current_state(self):
        return self.state_name(self.config, self.code_index, self.current)

    @property
    def next_state(self):
        return self.state_name(self.config, self.code_index, self.next)

    @property
    def vhdl(self):
        if self.splitter is not None:
            return self.PATTERN.format(
                current_state=self.current_state,
                current_state_name=self.config.current_state_name,
                next_state=self.next_state,
                wrong_code_state=self.config.wrong_code_state,
                print_fail=self.config.print_fail_state,
                next_state_name=self.config.next_state_name,
                next_state_branch='\n'.join(self._NEXT_STATE_BRANCH.format(
                    key=next_state_key,
                    next_state_name=self.config.next_state_name,
                    next_state=self.state_name(config, index, next_state_key)
                ) for index, next_state_key in enumerate(self.splitter, 1))
            )
        elif self.next:
            return self.PATTERN.format(
                current_state=self.current_state,
                current_state_name=self.config.current_state_name,
                next_state=self.next_state,
                wrong_code_state=self.config.wrong_code_state,
                print_fail=self.config.print_fail_state,
                next_state_name=self.config.next_state_name,
                next_state_branch=self._NEXT_STATE_BRANCH.format(
                    key=self.next,
                    next_state_name=self.config.next_state_name,
                    next_state=self.next_state
                )
            )

        return self.PATTERN_LAST_STATE.format(
            current_state=self.current_state,
            current_state_name=self.config.current_state_name,
            wrong_code_state=self.config.wrong_code_state,
            print_success=self.config.print_success_state,
            next_state_name=self.config.next_state_name,
        )


if __name__ == '__main__':
    config = Config.load()
    while not config:
        print("Invalid config.", file=stderr)
        config = Config.load()

    states = []
    for i, (num1, num2) in enumerate(zip(config.code1, config.code2)):
        is_next_same = config.code1[i + 1: i + 2] == config.code2[i + 1: i + 2]
        if num1 == num2:
            state = State(
                current_state_number=num1,
                next_state_number=config.code1[i + 1: i + 2] if is_next_same else None,
                config=config,
                code_index=0,
                splitter=(
                    config.code1[i + 1: i + 2],
                    config.code2[i + 1: i + 2],
                ) if not is_next_same else None
            )
            states.append(state)
            continue

        state1 = State(
            current_state_number=num1,
            next_state_number=config.code1[i + 1: i + 2],
            config=config,
            code_index=1,
        )
        state2 = State(
            current_state_number=num2,
            next_state_number=config.code2[i + 1: i + 2],
            config=config,
            code_index=2,
        )
        states.extend((state1, state2))

    print(FILE_PATTERN.format(
        code_states='\n\n'.join(state.vhdl for state in states),
        states_enum=', \n'.join(state.current_state for state in states),
        wrong_state=config.wrong_code_state,
        print_success=config.print_success_state,
        print_fail=config.print_fail_state,

    ))
