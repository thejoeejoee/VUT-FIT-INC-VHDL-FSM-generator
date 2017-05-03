#!/usr/bin/env python3
# coding=utf-8
from typing import Optional

FILE_PATTERN = """
architecture behavioral of fsm is
    type t_state is (
        TEST_0,
        TEST_1,
        TEST_2,
        TEST_3,
        TEST_4A, TEST_4B,
        TEST_5A, TEST_5B,
        TEST_6A, TEST_6B,
        TEST_7A, TEST_7B,
        TEST_8A, TEST_8B,
                 TEST_9B,
        WRONG_CODE, PRINT_ACCESS_DENIED,
        PRINT_ACCESS_ALLOWED,
        FINISH
    );
    signal present_state, next_state : t_state;
begin
-- -------------------------------------------------------
next_state_logic : process(present_state, KEY, CNT_OF)
begin
   case (present_state) is
   {code_states}
   when WRONG_CODE =>
      next_state <= WRONG_CODE;
      if pressed_enter_key then
         next_state <= PRINT_ACCESS_DENIED;
      end if;
   when PRINT_ACCESS_DENIED =>
      next_state <= PRINT_ACCESS_DENIED;
      if (CNT_OF = '1') then
         next_state <= FINISH;
      end if;
   when PRINT_ACCESS_ALLOWED =>
      next_state <= PRINT_ACCESS_ALLOWED;
      if (CNT_OF = '1') then
         next_state <= FINISH;
      end if;
   when FINISH =>
      next_state <= FINISH;
      if pressed_enter_key then
         next_state <= TEST_0;
      end if;
   when others =>
      next_state <= TEST_0;
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
        self.next_state = self.current_state = self.code_state_pattern = ""
        self.wrong_state = self.print_success_state = self.print_fail_state = ""

    @classmethod
    def load(cls):
        conf = Config()
        conf.next_state = input("Next state signal name [next_state]: ").strip() or 'next_state'
        conf.current_state = input("Current state signal name [current_state]: ").strip() or 'current_state'
        conf.code_state_pattern = input("Code state pattern [test_{code}]: ").strip() or 'test_{code}'

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
    PATTERN = """
    when {current_state} =>
        {next_state} <= {current_state};
        if (KEY(8) = '1') then
            {next_state} <= {next_state};
        elsif KEY(15) = '1' then
            {next_state} <= {print_fail};
        elsif KEY(15 downto 0) /= "0000000000000000" then
            {next_state} <= {wrong_code_state};
        end if;
    """
    PATTERN_LAST_STATE = """
    when {current_state} =>
        {next_state} <= {current_state};
        if KEY(15) = '1' then
            {next_state} <= {print_success};
        elsif KEY(15 downto 0) /= "0000000000000000" then
            {next_state} <= {wrong_code_state};
        end if;
    """

    def __init__(self, current_state_number: str, next_state_number: Optional[str], config: Config, code_index: int):
        self.current = current_state_number
        self.next = next_state_number
        self.config = config
        self.code_index = code_index

    @property
    def current_state_name(self):
        return self.config.code_state_pattern.format('_'.join(map(str, filter(None, (
            self.code_index,
            self.current
        )))))

    @property
    def next_state_name(self):
        return self.config.code_state_pattern.format('_'.join(map(str, filter(None, (
            self.code_index,
            self.next
        )))))

    @property
    def vhdl(self):
        if self.next:
            return self.PATTERN.format(
                current_state=self.current_state_name,
                next_state=self.next_state_name,
                wrong_code_state=self.config.wrong_state,
                print_fail=self.config.print_fail_state
            )

        return self.PATTERN_LAST_STATE.format(
            current_state=self.current_state_name,
            next_state=self.next_state_name,
            wrong_code_state=self.config.wrong_state,
            fail_state=self.config.print_fail_state
        )


if __name__ == '__main__':
    config = Config.load()
