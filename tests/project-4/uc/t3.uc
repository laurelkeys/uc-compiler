int main() {
    int n, r, temp;
    float sum = 0.;
    n = 5743475;
    temp = n;
    while(n > 0) {
        r = n % 10;
        sum = (sum * 10.) + (float)r;
        n = n / 10;
    }
    assert temp == (int)sum;
    return 0;
}
