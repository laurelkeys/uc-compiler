int main() {
    char s[] = "TajMahal.";
    int i = 0;
    int vowels = 0;
    int consonants = 0;

    while(s[i++] != '.') {
        if(s[i] == 'a' || s[i] == 'e' || s[i] == 'i' || s[i] == 'o' || s[i] == 'u' )
            vowels++;
        else
            consonants++;
    }

    assert vowels == 3 && consonants == 5;
    return 0;
}
