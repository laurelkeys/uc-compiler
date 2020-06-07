int main() {
    int i = 3, n = 6;
    for (int k = 1; k < n; k++) {
        if (i >= n) {
            break;
        }
        else {
            i++;
        }
    }
    assert i == n;
    return 0;
}
