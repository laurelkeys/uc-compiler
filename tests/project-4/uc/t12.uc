int main() {
    int a, b;

    a = 11;
    b = 99;

    a = a + b;
    b = a - b;
    a = a - b;

    assert a == 99 && b == 11;
    return 0;
}
