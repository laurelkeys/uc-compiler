// Armstrong number

int power (int n, int r) {
    int c, p = 1;
    for (c=1; c<=r; c++) {
        p = p*n;
    }
    return p; 
}

int main() {
    int n, sum = 0;
    int temp, remainder, digits = 0;

    n = 1634;
    temp = n;
    while (temp != 0) {
        digits += 1;
        temp = temp / 10;
    }
    temp = n;
    while (temp != 0) {
        remainder = temp % 10;
        sum = sum + power(remainder, digits);
        temp = temp / 10;
    }
    assert n == sum;
    return 0;
}
