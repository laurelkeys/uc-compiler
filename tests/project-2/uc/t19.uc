int m[][] = { {1,2}, {3,4}, {5,6} };

int main() {
    int sum = 0;
    for (int i=0; i<3; i++) {
        sum += m[i][0] + m[i][1];
    }
    assert sum == 21;
    return 0;
}
