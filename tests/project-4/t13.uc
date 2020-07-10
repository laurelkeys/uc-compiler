/* Bubble sort code */
int main() {
    int v[10] = {5, 3, 7, 8, 4, 1, 9, 2, 0, 6};
    int n = 10, c, d, swap;
    for (c = 0; c < n-1; c++)
        for (d = 0; d < n-c-1; d++)
            if (v[d] > v[d+1]) {
                swap = v[d];
                v[d] = v[d+1];
                v[d+1] = swap;
            }
    print("Sorted list in ascending order: ");
    for (c = 0; c < n; c++)
        print(v[c], " ");
    print();
    assert v[0] == 0 && v[9] == 9;
    return 0;
}
