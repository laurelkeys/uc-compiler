int checkPrime(int n) {
    int i, isPrime = 1;
    for (i = 2; i <= n/2; ++i) {
        if (n % i == 0) {
            isPrime = 0;
            break;
        }
    }
    return isPrime;
}

// void main() {} /* uncomment to use without -no-run */

// See https://raw.githubusercontent.com/iviarcio/mc921/27e4904b9bfff930d18baea819af1e4d75db95d9/checkPrime.gv.png