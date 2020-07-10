// Find the Transpose of a Matrix
int main() {
    int a[10][10], transpose[10][10], r, c, i, j;
    r = 5; c = 4;

    // Assigning elements to the matrix
    for (i = 0; i < r; ++i)
        for (j = 0; j < c; ++j) {
            a[i][j] = 10 + i*2 + j;
        }

    // Displaying the matrix a[][]
    print("Matrix:"); print();
    for (i = 0; i < r; ++i)
        for (j = 0; j < c; ++j) {
            print(a[i][j], "  ");
            if (j == c - 1)
                print();
        }

    // Finding the transpose of matrix a
    for (i = 0; i < r; ++i)
        for (j = 0; j < c; ++j) {
            transpose[j][i] = a[i][j];
        }

    // Displaying the transpose of matrix a
    print("Transpose of the matrix:"); print();
    for (i = 0; i < c; ++i)
        for (j = 0; j < r; ++j) {
            print(transpose[i][j], "  ");
            if (j == r - 1)
                print();
        }
    return 0;
}
