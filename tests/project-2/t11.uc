int main() {
    int x =2, y, z;
    y = ++x;
    z = x++;
    assert y == 3 && z == 3;
    return 0;
}
