import re

## regular expressions ####################################

# valid uC identifiers
identifier = r'[a-zA-Z_][0-9a-zA-Z_]*'

# integer constants
int_const = r'0|([1-9][0-9]*)' #r'[0-9]+'

# floating constants
float_const = r'((0|([1-9][0-9]*))\.[0-9]*|[0-9]*\.[0-9]+)' #r'([0-9]+\.[0-9]*|[0-9]*\.[0-9]+)'

# Comments in C-Style /* ... */
c_comment = r'/\*.*\*/'
c_comment_multiline = r'/\*(.|[\r\n])*?\*/'

# Unterminated C-style comment
unterminated_c_comment = r'/\*.*(?!\*/)' # FIXME

# C++-style comment (//...)
cpp_comment = r'//.*'

# string_literal
string_literal = r'\".*\"'

# unmatched_quote
unmatched_quote = r'\".*(?!\")$' # FIXME

## misc ###################################################

def fullmatches(match_obj):
    return match_obj is not None

## tests ##################################################

def test_identifier():
    assert fullmatches(re.fullmatch(identifier, "lcaseid"))
    assert fullmatches(re.fullmatch(identifier, "UCASEID"))
    assert fullmatches(re.fullmatch(identifier, "_underscode_id_"))
    assert fullmatches(re.fullmatch(identifier, "a1234"))
    assert not fullmatches(re.fullmatch(identifier, ""))
    assert not fullmatches(re.fullmatch(identifier, "01293"))
    assert not fullmatches(re.fullmatch(identifier, "_minus-sign"))
    assert not fullmatches(re.fullmatch(identifier, "foo!bar"))
    assert not fullmatches(re.fullmatch(identifier, "--arg"))

def test_int_const():
    #assert fullmatches(re.fullmatch(int_const, ""))
    pass

def test_float_const():
    #assert fullmatches(re.fullmatch(float_const, ""))
    pass

def test_c_comment():
    #assert fullmatches(re.fullmatch(c_comment, ""))
    pass

def test_c_comment_multiline():
    #assert fullmatches(re.fullmatch(c_comment_multiline, ""))
    pass

def test_unterminated_c_comment():
    #assert fullmatches(re.fullmatch(unterminated_c_comment, ""))
    pass

def test_cpp_comment():
    #assert fullmatches(re.fullmatch(cpp_comment, ""))
    pass

def test_string_literal():
    #assert fullmatches(re.fullmatch(string_literal, ""))
    pass

def test_unmatched_quote():
    #assert fullmatches(re.fullmatch(unmatched_quote, ""))
    pass
