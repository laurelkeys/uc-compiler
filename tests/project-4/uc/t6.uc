int main(){
    int v[] = {1, 2, 3, 4, 5};
    char c[] = "xpto";
    char w[4];
    int i = 2, j = 3, k = 4;
    w[2] = c[1];
    v[i] = i + j + k;
    j = j - 2;
    assert w[i] == c[j] && v[i] == 9;
    return 0;
}
