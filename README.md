# VUT FIT INC - FSM state generator

Skript sloužící k automatické vygenerování stavů pro [stavový automat](https://cs.wikipedia.org/wiki/Kone%C4%8Dn%C3%BD_automat) řídící přístupový terminál jako projekt do předmětu INC.

## Použití
```bash
$ git clone https://github.com/thejoeejoee/VUT-FIT-INC-VHDL-FSM-generator.git
$ cd VUT-FIT-INC-VHDL-FSM-generator
$ ./fsm_generator.py
Next state signal name [next_state]: 
Current state signal name [current_state]: 
Code state pattern [test_{code}]:  
Wrong code state name [wrong_code]: 
State to print success [print_success]: 
State to print success [print_fail]: 
Code 1: 42 
Code 2:
File to write [fsm_state.vhd]: 
SUCCESS: Generated states written fsm_state.vhd.
WARNING: It's neccessary to define cases for print_success, print_fail and wrong_code and implement proccesses for output logic and sync_logic!

$ cat fsm_state.vhd

when TEST_0 =>
    next_state <= test_0;
    if (KEY(4) = '1') then
        next_state <= test_1;
    elsif pressed_enter_key then
        next_state <= print_fail;
    elsif pressed_code_key then
        next_state <= wrong_code;
    end if;
when TEST_1 =>
    next_state <= test_1;
    if (KEY(2) = '1') then
        next_state <= test_2;
    elsif pressed_enter_key then
        next_state <= print_fail;
    elsif pressed_code_key then
        next_state <= wrong_code;
    end if;
when TEST_2 =>
    next_state <= test_2;
    if pressed_enter_key then
        next_state <= print_success;
    elsif pressed_code_key then
        next_state <= wrong_code;
    end if;
```