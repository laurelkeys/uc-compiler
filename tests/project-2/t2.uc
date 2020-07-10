int n = 3;

int doubleMe (int x) {
    return x * x;
}

void main () {
    int v = n;
    v = doubleMe (v);
    assert v == n * n;
    return 0;
}