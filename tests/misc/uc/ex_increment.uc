int main () {
    int x = 2, y, z;
    y = ++x;
    z = x++;
    assert x == 4 && y == z;
    return 1;
}