// Store Numbers and Calculate Average Using Arrays
int main() {
    int n, i;
    float num[100], sum = 0.0, avg;

    print("Enter the numbers of elements: ");
    read(n);

    while (n > 100 || n < 1) {
        print("Error! number should in range of (1 to 100).\n");
        print("Enter the number again: ");
        read(n);
    }

    for (i = 0; i < n; ++i) {
        print(i + 1, "Enter number: ");
        read(num[i]);
        sum = sum + num[i];
    }

    avg = sum / n;
    print("Average = ", avg);
    return 0;
}