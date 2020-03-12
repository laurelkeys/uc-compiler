import re

###########################################################
## regular expressions ####################################
###########################################################

# valid uC identifiers
identifier = r'[a-zA-Z_][0-9a-zA-Z_]*'

# integer constants
int_const = r'0|([1-9][0-9]*)'
int_const_0s = r'[0-9]+' # accepts leading zeros

# floating constants
float_const = r'((0|([1-9][0-9]*))\.[0-9]*)|((|0|([1-9][0-9]*))\.[0-9]+)'
float_const_0s = r'([0-9]+\.[0-9]*|[0-9]*\.[0-9]+)' # accepts leading zeros

# Comments in C-Style /* ... */
c_comment = r'/\*(.|\n)*?\*/'

# Unterminated C-style comment
unterminated_c_comment = r'/\*(.|\n)*?(?<!\*/)$'

# C++-style comment (//...)
cpp_comment = r'//.*'

# string_literal
string_literal = r'".*"'

# unmatched_quote
unmatched_quote = r'".*(?<!")$'

###########################################################
## misc ###################################################
###########################################################

def fullmatches(match_obj):
    return match_obj is not None

###########################################################
## tests ##################################################
###########################################################

def test_identifier():
    assert not fullmatches(re.fullmatch(identifier, ""))
    assert fullmatches(re.fullmatch(identifier, "_"))
    assert fullmatches(re.fullmatch(identifier, "a"))
    assert fullmatches(re.fullmatch(identifier, "abcd"))
    assert fullmatches(re.fullmatch(identifier, "ABCD"))
    assert fullmatches(re.fullmatch(identifier, "a1234"))
    assert fullmatches(re.fullmatch(identifier, "_aB123_"))
    assert not fullmatches(re.fullmatch(identifier, "123"))
    assert not fullmatches(re.fullmatch(identifier, "a-bc"))
    assert not fullmatches(re.fullmatch(identifier, "foo!bar"))

def test_int_const():
    assert not fullmatches(re.fullmatch(int_const, ""))
    assert fullmatches(re.fullmatch(int_const, "0"))
    assert fullmatches(re.fullmatch(int_const, "10"))
    assert fullmatches(re.fullmatch(int_const, "123"))
    assert not fullmatches(re.fullmatch(int_const, "001"))
    assert not fullmatches(re.fullmatch(int_const, "0001"))
    assert not fullmatches(re.fullmatch(int_const, "1o24"))

def test_float_const():
    assert not fullmatches(re.fullmatch(float_const, ""))
    assert fullmatches(re.fullmatch(float_const, "0."))
    assert fullmatches(re.fullmatch(float_const, ".12"))
    assert fullmatches(re.fullmatch(float_const, "0.12"))
    assert not fullmatches(re.fullmatch(float_const, "."))
    assert not fullmatches(re.fullmatch(float_const, "01."))
    assert not fullmatches(re.fullmatch(float_const, "01.2"))
    assert not fullmatches(re.fullmatch(float_const, "0"))
    assert not fullmatches(re.fullmatch(float_const, "123"))
    assert not fullmatches(re.fullmatch(float_const, "0_12"))

def test_c_comment():
    assert not fullmatches(re.fullmatch(c_comment, ""))
    assert fullmatches(re.fullmatch(c_comment, "/**/"))
    assert fullmatches(re.fullmatch(c_comment, "/***/"))
    assert fullmatches(re.fullmatch(c_comment, "/* */"))
    assert fullmatches(re.fullmatch(c_comment, "/*asdf*/"))
    assert fullmatches(re.fullmatch(c_comment, "/* asdf */"))
    assert fullmatches(re.fullmatch(c_comment, "/*a!@#45^&)[@!_*/"))
    assert fullmatches(re.fullmatch(c_comment, """/*
                                                   * foo
                                                   * bar
                                                   * baz
                                                   **/"""))
    assert not fullmatches(re.fullmatch(c_comment, "/* foo"))
    assert not fullmatches(re.fullmatch(c_comment, "// foo"))
    assert not fullmatches(re.fullmatch(c_comment, "/* * /"))
    assert not fullmatches(re.fullmatch(c_comment, "/ * */"))
    assert not fullmatches(re.fullmatch(c_comment, "/** foo"))
    assert not fullmatches(re.fullmatch(c_comment, """/* 
                                                      xpto
                                                   """))

def test_unterminated_c_comment():
    assert not fullmatches(re.fullmatch(unterminated_c_comment, ""))
    assert not fullmatches(re.fullmatch(unterminated_c_comment, ""))
    assert not fullmatches(re.fullmatch(unterminated_c_comment, "/**/"))
    assert not fullmatches(re.fullmatch(unterminated_c_comment, "/***/"))
    assert not fullmatches(re.fullmatch(unterminated_c_comment, "/* */"))
    assert not fullmatches(re.fullmatch(unterminated_c_comment, "/*asdf*/"))
    assert not fullmatches(re.fullmatch(unterminated_c_comment, "/* asdf */"))
    assert not fullmatches(re.fullmatch(unterminated_c_comment, "/*a!@#45^&)[@!_*/"))
    assert not fullmatches(re.fullmatch(unterminated_c_comment, "// foo"))
    assert not fullmatches(re.fullmatch(unterminated_c_comment, "/ * */"))
    assert fullmatches(re.fullmatch(unterminated_c_comment, "/*"))
    assert fullmatches(re.fullmatch(unterminated_c_comment, "/**"))
    assert fullmatches(re.fullmatch(unterminated_c_comment, "/* "))
    assert fullmatches(re.fullmatch(unterminated_c_comment, "/*asdf"))
    assert fullmatches(re.fullmatch(unterminated_c_comment, "/* * /"))
    assert fullmatches(re.fullmatch(unterminated_c_comment, "/* foo"))
    assert fullmatches(re.fullmatch(unterminated_c_comment, "/** foo"))
    assert fullmatches(re.fullmatch(unterminated_c_comment, "/* asdf "))
    assert fullmatches(re.fullmatch(unterminated_c_comment, "/*a!@#45^&)[@!_"))

def test_cpp_comment():
    assert not fullmatches(re.fullmatch(cpp_comment, ""))
    assert fullmatches(re.fullmatch(cpp_comment, "//"))
    assert fullmatches(re.fullmatch(cpp_comment, "///"))
    assert fullmatches(re.fullmatch(cpp_comment, "// asdf"))
    assert fullmatches(re.fullmatch(cpp_comment, "// asdf ///"))
    assert fullmatches(re.fullmatch(cpp_comment, "// /* asdf */"))
    assert not fullmatches(re.fullmatch(cpp_comment, "/ //"))
    assert not fullmatches(re.fullmatch(cpp_comment, "/* // */"))

def test_string_literal():
    assert not fullmatches(re.fullmatch(string_literal, ""))
    assert fullmatches(re.fullmatch(string_literal, "\"\""))
    assert fullmatches(re.fullmatch(string_literal, "\" \""))
    assert fullmatches(re.fullmatch(string_literal, "\"\"\"\""))
    assert fullmatches(re.fullmatch(string_literal, "\"\'\'\""))
    assert fullmatches(re.fullmatch(string_literal, "\"asdf1234!@#$])\""))
    assert not fullmatches(re.fullmatch(string_literal, "\'\'"))
    assert not fullmatches(re.fullmatch(string_literal, "\' \'"))
    assert not fullmatches(re.fullmatch(string_literal, "\'\"\"\'"))
    assert not fullmatches(re.fullmatch(string_literal, "\'asdf1234!@#$])\'"))

def test_unmatched_quote():
    assert not fullmatches(re.fullmatch(unmatched_quote, ""))
    # assert fullmatches(re.fullmatch(unmatched_quote, "\"")) # FIXME should this be a match?
    assert fullmatches(re.fullmatch(unmatched_quote, "\" "))
    # assert fullmatches(re.fullmatch(unmatched_quote, "\"\"\"")) # FIXME should this be a match?
    assert fullmatches(re.fullmatch(unmatched_quote, "\"\'\'"))
    assert fullmatches(re.fullmatch(unmatched_quote, "\"asdf1234!@#$])"))
    assert not fullmatches(re.fullmatch(unmatched_quote, "\"\""))
    assert not fullmatches(re.fullmatch(unmatched_quote, "\" \""))
    assert not fullmatches(re.fullmatch(unmatched_quote, "\"\"\"\""))
    assert not fullmatches(re.fullmatch(unmatched_quote, "\"\'\'\""))
    assert not fullmatches(re.fullmatch(unmatched_quote, "\"asdf1234!@#$])\""))
    assert not fullmatches(re.fullmatch(unmatched_quote, "\'\'"))
    assert not fullmatches(re.fullmatch(unmatched_quote, "\' \'"))
    assert not fullmatches(re.fullmatch(unmatched_quote, "\'\"\"\'"))
    assert not fullmatches(re.fullmatch(unmatched_quote, "\'asdf1234!@#$])\'"))
