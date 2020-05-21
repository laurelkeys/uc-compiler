// Find the Transpose of a Matrix
int main() {
    int a[10][10], transpose[10][10], r, c, i, j;
    print("Enter rows and columns: ");
    read(r, c);

    // Assigning elements to the matrix
    print("\nEnter matrix elements:\n");
    for (i = 0; i < r; ++i)
        for (j = 0; j < c; ++j) {
            print("Enter element [", i + 1, j + 1, "]: ");
            read(a[i][j]);
        }

    // Displaying the matrix a[][]
    print("\nEntered matrix: \n");
    for (i = 0; i < r; ++i)
        for (j = 0; j < c; ++j) {
            print(a[i][j]);
            if (j == c - 1)
                print();
        }

    // Finding the transpose of matrix a
    for (i = 0; i < r; ++i)
        for (j = 0; j < c; ++j) {
            transpose[j][i] = a[j];
        }

    // Displaying the transpose of matrix a
    print("\nTranspose of the matrix:\n");
    for (i = 0; i < c; ++i)
        for (j = 0; j < r; ++j) {
            print(transpose[i][j]);
            if (j == r - 1)
                print();
        }
    return 0;
}