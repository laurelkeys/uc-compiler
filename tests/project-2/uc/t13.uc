int main(){
    int v[] = {1, 2, 3, 4, 5};
    int i = 2;
    char c[] = "xpto";
    char w[4];
    w[2] = c[1];
    v[i] = 9;
    assert w[i] == c[1] && v[i] == 9;
    return 0;
}
