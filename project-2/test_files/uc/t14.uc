int fat(int n) {
    if (n <= 1)
        return 1;
    else
        return n * fat(n-1);
}

int main() {
    int x = 7;
    assert fat(x) == 5040;
    return 0;
}
