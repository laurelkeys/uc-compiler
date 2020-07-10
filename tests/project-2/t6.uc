int main() {
    int n, r, temp;
    float sum = 0.;
    print("enter the number = ");
    read(n);
    temp = n;
    while(n > 0) {
        r = n % 10;
        sum = (sum * 10.) + (float)r;
        n = n / 10;
    }
    if(temp == sum)
        print("palindrome number ");
    else
        print("not palindrome");
    return 0;
}