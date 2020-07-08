/* Check Armstrong Numbers */

int power(int n, int r);

int armstrong(int n);

int main () {
    int n1 = 407, n2 = 1634;   // armstrong numbers
    int n3 = 8207;             // not an Armstrong. (8208)
    assert armstrong(n1) == 1;
    assert armstrong(n2) == 1;
    assert armstrong(n3) == 0;
    assert armstrong(153) == 1;
    return 0;
}

int power(int n, int r) {
  int p = 1;
  for (int c = 1; c <= r; c++)
      p = p*n;
  return p;
}

int armstrong(int n) {
    int temp, remainder;
    int sum = 0, digits = 0;
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
    if (n == sum)
        return 1;
    else
        return 0;
}

