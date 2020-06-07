int v[] = {1, 2, 3, 4};
void main(){
    int sum;
    for (int i = 0; i < 4; i++)
        sum = sum + v[i];
    assert sum == 10;
    return;
}