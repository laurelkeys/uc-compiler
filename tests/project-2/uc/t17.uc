/* Bubble sort code */

int main() {
    int v[10];
    int n = 6, c, d, swap;
    for (c = 0; c < n; c++)
        v[c] = 10 - c;
    for (c = 0; c < n-1; c++)
        for (d = 0; d < n-c-1; d++)
            if (v[d] = v[d+1]) {
                swap = v[d];
                v[d] = v[d+1];
                v[d+1] = swap;
            }
    for (c = 0; c < n; c++)
        assert v[c] == c + 5;
    return 0;
}
