int main() {
    int n, t1 = 0, t2 = 1, nextTerm;
    print("Enter the number of terms: ");
    read(n);
    print("Fibonacci Series: ");

    for (i = 1; i <= n; ++i) {
        print(t1, " ");
        nextTerm = t1 + t2;
        t1 = t2;
        t2 = nextTerm;
    }

    return 0;
}