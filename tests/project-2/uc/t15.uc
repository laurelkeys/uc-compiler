int z = 3, t =4;

int g (int t) {
 int x;
 t *= 2;
 x = 2*t;
 z = x+1;
 return x;
}

int main(){
    int i, j, k;
    i = g(t);
    j = g(z);
    k = g(t+z);
    assert i == 16 && j == 68 && k == 292;
    return 0;
}
