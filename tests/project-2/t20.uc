int checkPrime(int n);

int main() {
    int n, i, flag = 0;
    n = 190;
    for (i = 2; i <= n / 2; ++i) {
        // condition for i to be a prime number
        if (checkPrime(i) == 1) {
            // condition for n-i to be a prime number
            if (checkPrime(n - i) == 1) {
                flag = 1;
            }
        }
    }
    assert flag == 1;
    return 0;
}

// function to check prime number
int checkPrime(int n) {
    int i, isPrime = 1;
    for (i = 2; i <= n / 2; ++i) {
        if (n % i == 0) {
            isPrime = 0;
            break;
        }
    }
    return isPrime;
}
