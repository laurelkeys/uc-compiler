int n = 10;

int foo(int a, int b) {
    return n * (a + b);
}

int main() {
    int c = 2, d = 3;
    int e = foo(c, d);
    assert e == 50;
    return 0;
}
