int main() {
    int n, reverse = 0, rem;
    print("Enter a number: ");
    read(n);
    while (n != 0) {
        rem = n % 10;
        reverse = reverse * 10 + rem;
        n /= 10;
    }
    print("Reversed Number: ", reverse);
    return 0;
}