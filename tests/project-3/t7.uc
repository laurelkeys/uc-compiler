/* Compute GCD of two integers */

int gcd (int x, int y) {
    int g = y;
    while (x > 0) {
        g = x;
	    x = y - (y/x) * x;
	    y = g;
    }
    return g;
}

void main() {
    int a = 198, b;
    b = 36;
    assert gcd(a, b) == 18;
    return;
}
