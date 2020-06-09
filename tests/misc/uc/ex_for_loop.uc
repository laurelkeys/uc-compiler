int main () {
    int i, j;
    i = 1;
    j = 2;
    for (int k=1; k<10; k++)
        i += j * k;
    assert i == 91;
    return 0;
}