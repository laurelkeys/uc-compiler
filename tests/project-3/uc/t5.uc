int main() {
    int n = 1, reverse = 0, rem;
    n += 17327; 
    while (n > 0) {
        rem = n % 10;
        reverse = reverse * 10 + rem;
        n = n / 10;
    }
    assert reverse == 82371;
    return 0;
}