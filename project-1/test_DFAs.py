
###########################################################
## DFA (deterministic finite automata) ####################
###########################################################

class DFA:

    def __init__(self, states, alphabet, transition_function, start_state, accept_states):
        self.states = states
        self.alphabet = alphabet
        self.transition_function = transition_function
        self.start_state = start_state
        self.accept_states = accept_states
        self.current_state = start_state

    def transition_to_state_with_input(self, input_value):
        if (self.current_state, input_value) not in self.transition_function:
            self.current_state = None
            return
        self.current_state = self.transition_function[(self.current_state, input_value)]

    def in_accept_state(self):
        return self.current_state in self.accept_states

    def go_to_initial_state(self):
        self.current_state = self.start_state

    def run_with_input_list(self, input_list):
        self.go_to_initial_state()
        for inp in input_list:
            self.transition_to_state_with_input(inp)
        return self.in_accept_state()

###########################################################
## misc ###################################################
###########################################################

tf = dict()
tf[(0, 'a')] = 1; tf[(0, 'b')] = 2; tf[(0, 'c')] = 3; tf[(0, 'd')] = 0
tf[(1, 'a')] = 1; tf[(1, 'b')] = 2; tf[(1, 'c')] = 3; tf[(1, 'd')] = 0
tf[(2, 'a')] = 1; tf[(2, 'b')] = 2; tf[(2, 'c')] = 3; tf[(2, 'd')] = 0
tf[(3, 'a')] = 1; tf[(3, 'b')] = 2; tf[(3, 'c')] = 3; tf[(3, 'd')] = 0

d = DFA(
        states={0, 1, 2, 3},
        alphabet={'a', 'b', 'c', 'd'},
        transition_function=tf,
        start_state=0,
        accept_states={2, 3}
    )

# All strings over {a, b, c} that contain an odd number of b's
tf = dict()
tf[(0, 'a')] = 0; tf[(0, 'b')] = 1; tf[(0, 'c')] = 0
tf[(1, 'a')] = 1; tf[(1, 'b')] = 0; tf[(1, 'c')] = 1

odd_b = DFA(
        states={0, 1},
        alphabet={'a', 'b', 'c'},
        transition_function=tf,
        start_state=0,
        accept_states={1}
    )

# All strings over {a, b, c} that contain an even number of a's and an odd number of b's
tf = dict()
tf[(0, 'a')] = 2; tf[(0, 'b')] = 1; tf[(0, 'c')] = 0 # state 0: even a's and even b's
tf[(1, 'a')] = 3; tf[(1, 'b')] = 0; tf[(1, 'c')] = 1 # state 1: even a's and  odd b's
tf[(2, 'a')] = 0; tf[(2, 'b')] = 3; tf[(2, 'c')] = 2 # state 2:  odd a's and even b's
tf[(3, 'a')] = 1; tf[(3, 'b')] = 2; tf[(3, 'c')] = 3 # state 3:  odd a's and  odd b's

even_a_odd_b = DFA(
        states={0, 1, 2, 3},
        alphabet={'a', 'b', 'c'},
        transition_function=tf,
        start_state=0,
        accept_states={1}
    )

# All strings over {a, b, c, d} of length at least 2 whose second symbol does not appear elsewhere in the string
tf = dict()
tf[(0, 'a')] = 1; tf[(0, 'b')] = 2; tf[(0, 'c')] = 3; tf[(0, 'd')] = 4

tf[(1, 'b')] = 6; tf[(1, 'c')] = 7; tf[(1, 'd')] = 8
tf[(2, 'a')] = 5; tf[(2, 'c')] = 7; tf[(2, 'd')] = 8
tf[(3, 'a')] = 5; tf[(3, 'b')] = 6; tf[(3, 'd')] = 8
tf[(4, 'a')] = 5; tf[(4, 'b')] = 6; tf[(4, 'c')] = 7

tf[(5, 'b')] = 5; tf[(5, 'c')] = 5; tf[(5, 'd')] = 5
tf[(6, 'a')] = 6; tf[(6, 'c')] = 6; tf[(6, 'd')] = 6
tf[(7, 'a')] = 7; tf[(7, 'b')] = 7; tf[(7, 'd')] = 7
tf[(8, 'a')] = 8; tf[(8, 'b')] = 8; tf[(8, 'c')] = 8

len_2_unique_second = DFA(
        states={0, 1, 2, 3, 4, 5, 6, 7, 8},
        alphabet={'a', 'b', 'c', 'd'},
        transition_function=tf,
        start_state=0,
        accept_states={5, 6, 7, 8}
    )

###########################################################
## tests ##################################################
###########################################################

def test_dfa():
    assert not d.run_with_input_list("")
    assert d.run_with_input_list("abcabdc")
    assert not d.run_with_input_list("abcdabcdabcd")

def test_odd_b():
    assert not odd_b.run_with_input_list("")
    assert odd_b.run_with_input_list("b")
    assert odd_b.run_with_input_list("bbb")
    assert odd_b.run_with_input_list("abc")
    assert odd_b.run_with_input_list("abbcab")
    assert odd_b.run_with_input_list("abcabcabc")
    assert not odd_b.run_with_input_list("bb")
    assert not odd_b.run_with_input_list("bbbab")
    assert not odd_b.run_with_input_list("abcabc")

def test_even_a_odd_b():
    assert not even_a_odd_b.run_with_input_list("")
    assert even_a_odd_b.run_with_input_list("b")
    assert even_a_odd_b.run_with_input_list("bbb")
    assert even_a_odd_b.run_with_input_list("aba")
    assert even_a_odd_b.run_with_input_list("abca")
    assert even_a_odd_b.run_with_input_list("abbcab")
    assert not even_a_odd_b.run_with_input_list("aa")
    assert not even_a_odd_b.run_with_input_list("abc")
    assert not even_a_odd_b.run_with_input_list("abcabcabc")

def test_len_2_unique_second():
    assert not len_2_unique_second.run_with_input_list("")
    assert len_2_unique_second.run_with_input_list("bdabc")
    assert len_2_unique_second.run_with_input_list("acbab")
    assert len_2_unique_second.run_with_input_list("bacbd")
    assert len_2_unique_second.run_with_input_list("abcdc")
    assert not len_2_unique_second.run_with_input_list("aa")
    assert not len_2_unique_second.run_with_input_list("dd")
    assert not len_2_unique_second.run_with_input_list("bcabc")
    assert not len_2_unique_second.run_with_input_list("abcbc")
