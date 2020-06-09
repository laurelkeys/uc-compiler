int main() {
    int i = 3, n = 6;
    for (int k = 1; k < n; k++) {
        if (i >= n) {
            break;
        }
        else {
            i++;
        }
    }
    assert i == n;
    return 0;
}

// See https://raw.githubusercontent.com/iviarcio/mc921/27e4904b9bfff930d18baea819af1e4d75db95d9/opt_ex1.png