/* Palindrome numbers: */

int main() {
    int n,t, reverse = 0;
    n = 12321;
    t = n;
    while (t != 0) {
        reverse = reverse * 10;
        reverse = reverse + t % 10;
        t = t / 10;
    }
    assert n == reverse;
    return 0;
}
