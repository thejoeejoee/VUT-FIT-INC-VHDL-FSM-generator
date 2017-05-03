# VUT FIT INC - FSM state generator

Skript sloužící k automatické vygenerování stavů pro [stavový automat](https://cs.wikipedia.org/wiki/Kone%C4%8Dn%C3%BD_automat) řídící přístupový terminál jako projekt do předmětu INC. Vygenerovaný kód slouží pouze jako inspirace a je nutné jej doplnit o některé náležitosti týkající se FSM.

## Stažení
```bash
$ git clone https://github.com/thejoeejoee/VUT-FIT-INC-VHDL-FSM-generator.git
$ cd VUT-FIT-INC-VHDL-FSM-generator
```
## Použití
Při spuštění scriptu jste tázáni k zadání návů signálů, pomocných stavů FSM a Vašich kódů k přístupovému terminálu. Všechny hodnoty kromě kódů mají svou výchozí hodnotu, která je použita při nezadání konkrétní hodnoty.
```bash
$ ./fsm_generator.py 
Next state signal name [next_state]: 
Present state signal name [present_state]: 
Code state pattern [test_{}]: 
Wrong code state name [wrong_code]: 
State to print success [print_success]: 
State to print success [print_fail]: 
State to finish [finish]: 
File to write [output.vhd]: 
Code 1: 42
Code 2: 48
SUCCESS: Generated states written output.vhd.
$ cat output.vhd
architecture behavioral of fsm is
    type t_state is (
        test_0_0, 
        test_1_0, 
        test_2_1, 
        test_2_2,

        wrong_code_state,
        print_fail,
        print_success,
        finish
    );
    signal present_state, next_state : t_state;
begin
-- -------------------------------------------------------
next_state_logic : process(present_state, KEY, CNT_OF)
begin
   case (present_state) is
   
    when test_0_0 =>
        next_state <= test_0_0;
        if KEY(15) = '1' then
            next_state <= print_fail;
        elsif KEY(15 downto 0) /= "0000000000000000" then
            next_state <= wrong_code_state;
        
        if (KEY(4) = '1') then
            next_state <= test_1_0;
        end if;
        end if;

    when test_1_0 =>
        next_state <= test_1_0;
        if KEY(15) = '1' then
            next_state <= print_success;
        elsif KEY(15 downto 0) /= "0000000000000000" then
            next_state <= wrong_code_state;
        
        if (KEY(2) = '1') then
            next_state <= test_2_1;
        end if;

        if (KEY(8) = '1') then
            next_state <= test_2_2;
        end if;
        end if;

    when test_2_1 =>
        next_state <= test_2_1;
        if KEY(15) = '1' then
            next_state <= print_success;
        elsif KEY(15 downto 0) /= "0000000000000000" then
            next_state <= wrong_code_state;
        end if;

    when test_2_2 =>
        next_state <= test_2_2;
        if KEY(15) = '1' then
            next_state <= print_success;
        elsif KEY(15 downto 0) /= "0000000000000000" then
            next_state <= wrong_code_state;
        end if;

    when wrong_code_state =>
        next_state <= wrong_code_state;
        if KEY(15) = '1' then
            next_state <= print_fail;
        end if;
    when print_success =>
        next_state <= print_success;
        if (CNT_OF = '1') then
            next_state <= finish;
        end if;
    when print_fail =>
        next_state <= print_fail;
        if (CNT_OF = '1') then
            next_state <= finish;
        end if;
    when finish =>
        next_state <= finish;
        if KEY(15) = '1' then
            next_state <= test_0_0;
        end if;
    when others =>
        next_state <= test_0_0;
   end case;
end process next_state_logic;

-- TODO sync logic
-- TODO output logic

end architecture behavioral;

```