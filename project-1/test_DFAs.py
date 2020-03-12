
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
        return self.current_state in accept_states

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

states = { 0, 1, 2, 3 }
alphabet = { 'a', 'b', 'c', 'd' }

start_state = 0
accept_states = { 2, 3 }

tf = dict()
tf[(0, 'a')] = 1; tf[(0, 'b')] = 2; tf[(0, 'c')] = 3; tf[(0, 'd')] = 0
tf[(1, 'a')] = 1; tf[(1, 'b')] = 2; tf[(1, 'c')] = 3; tf[(1, 'd')] = 0
tf[(2, 'a')] = 1; tf[(2, 'b')] = 2; tf[(2, 'c')] = 3; tf[(2, 'd')] = 0
tf[(3, 'a')] = 1; tf[(3, 'b')] = 2; tf[(3, 'c')] = 3; tf[(3, 'd')] = 0
d = DFA(states, alphabet, tf, start_state, accept_states)

# All strings over {a, b, c} that contain an odd number of b's
tf = dict()
odd_b = DFA(states, alphabet, tf, start_state, accept_states)

# All strings over {a, b, c} that contain an even number of a's and an odd number of b's
tf = dict()
even_a_odd_b = DFA(states, alphabet, tf, start_state, accept_states)

# All strings over {a, b, c, d} of length at least 2 whose second symbol does not appear elsewhere in the string
tf = dict()
len_2_unique_second = DFA(states, alphabet, tf, start_state, accept_states)

###########################################################
## tests ##################################################
###########################################################

def test_dfa():
    assert not d.run_with_input_list("")
    assert d.run_with_input_list("abcabdc")
    assert not d.run_with_input_list("abcdabcdabcd")

def test_odd_b():
    assert not d.run_with_input_list("")
    assert d.run_with_input_list("b")
    assert d.run_with_input_list("bbb")
    assert d.run_with_input_list("abc")
    assert d.run_with_input_list("abbcab")
    assert d.run_with_input_list("abcabcabc")
    assert not d.run_with_input_list("d")
    assert not d.run_with_input_list("db")
    assert not d.run_with_input_list("bb")
    assert not d.run_with_input_list("bbbab")
    assert not d.run_with_input_list("abcabc")

def test_even_a_odd_b():
    assert not d.run_with_input_list("")
    assert d.run_with_input_list("b")
    assert d.run_with_input_list("bbb")
    assert d.run_with_input_list("aba")
    assert d.run_with_input_list("abca")
    assert d.run_with_input_list("abbcab")
    assert not d.run_with_input_list("d")
    assert not d.run_with_input_list("aa")
    assert not d.run_with_input_list("abc")
    assert not d.run_with_input_list("abcabcabc")

def test_len_2_unique_second():
    assert not d.run_with_input_list("")
    assert d.run_with_input_list("bdabc")
    assert d.run_with_input_list("acbab")
    assert d.run_with_input_list("bacbd")
    assert d.run_with_input_list("abcdc")
    assert not d.run_with_input_list("aa")
    assert not d.run_with_input_list("dd")
    assert not d.run_with_input_list("bcabc")
    assert not d.run_with_input_list("abcbc")
