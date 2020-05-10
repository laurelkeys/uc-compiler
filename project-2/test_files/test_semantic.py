import sys, os, filecmp, unittest, re
from io import StringIO 
from difflib import unified_diff as diff
from contextlib import contextmanager
from importlib.machinery import SourceFileLoader

workdir = os.path.dirname(os.path.abspath(__file__))
test_file = workdir + "/test.uc"
workdir = re.sub('.tests.unittest$', '', workdir)
sys.path.append(workdir[:])
import uCCompiler

class TestAST(unittest.TestCase):

    def runNcmp(self, code, err_test=True):
        f = open(test_file, "w")
        f.write(code)
        f.flush()
        f.close()

        sys.argv = sys.argv[:1]+[test_file]
        with self.assertRaises(SystemExit) as cm:
            uCCompiler.run_compiler()
        err = cm.exception.code

        if err_test != err : 
            if err_test : raise Exception("An error should've ocurred\n")
            else : raise Exception("There should be no errors\n")
            
        print("==================")
        
    def test_f1(self):
        self.runNcmp(
        '''
        int main(){
            return;
        }
        '''
        , err_test=True)

    # Predefined Funcions

    def test_pf1(self):
        self.runNcmp(
        '''
        int v = 1;
        char str[10] = "some/path";

        void main() {
            print();
            print("veri", 123, "naice", 0.2, 'h');
            assert(v==1);
            assert((v==1 && v!=0) || !(v==v) );
            read(v);
            read("uat");
        }
        '''
        , err_test=False)

    def test_pf2(self):
        self.runNcmp(
        '''
        void test() {
            assert("uaaat");
        }
        '''
        , err_test=True)

    def test_pf3(self):
        self.runNcmp(
        '''
        void test() {
            print(d);
        }
        '''
        , err_test=True)


    # Functions

    def test_f2(self):
        self.runNcmp(
        '''
        int test(int a, float b, char c);
        int test(int a, float b, char c);
        '''
        , err_test=False)

    def test_f3(self):
        self.runNcmp(
        '''
        int test(int a, float b, char c);
        int test(int a, int b, char c);
        '''
        , err_test=True)

    def test_f4(self):
        self.runNcmp(
        '''
        int test(int a, float b, char c);
        int test(int a, int b, char c) {
            return 0;
        }
        '''
        , err_test=True)

    def test_f5(self):
        self.runNcmp(
        '''
        int test(int a, float b, char c);
        int test(int a, float b, char c) {
            return 0;
        }
        '''
        , err_test=False)

    def test_f6(self):
        self.runNcmp(
        '''
        int test(int a, float b, char c){
            return 0;
        }

        int test(int a, float b, char c) {
            return 0;
        }
        '''
        , err_test=True)

    def test_f7(self):
        self.runNcmp(
        '''
        int test(int a, float b, char c){
            
        }
        '''
        , err_test=True)
    
    def test_f8(self):
        self.runNcmp(
        '''
        void test(int a, float b, char c){
            
        }

        void test2(int a, float b, char c){
            return;
        }
        '''
        , err_test=False)

    def test_f9(self):
        self.runNcmp(
        '''
        void test(int a, float b, char c){
            test2();
        }

        void test2(int a, float b, char c){
            return;
        }
        '''
        , err_test=True)

    def test_f10(self):
        self.runNcmp(
        '''
        void test2 (int a, float b, char c);

        void test(int a, float b, char c){
            test2 (1, 1.0, '1');
        }

        void test2(int a, float b, char c){
            return;
        }
        '''
        , err_test=False)

    def test_f11(self):
        self.runNcmp(
        '''
        void test2 (int a, float b, char c);

        void test(int a, float b, char c){
            test2 (1, 1.0, '1');
        }
        '''
        , err_test=True)

    def test_f12(self):
        self.runNcmp(
        '''
        void test2 (int a, float b, char c);

        void test(int a, float b, char c){
            int x;
            float y;
            char z;
            test2 (x, y, z);
        }

        void test2(int a, float b, char c){
            return;
        }
        '''
        , err_test=False)

    # Variables
    
    def test_v0(self):
        self.runNcmp(
        '''
        int x = 1;

        void main () {
            float f = -.1, f2 = +0.3;
            f *= 0.01;
            f2 /= 123.0;
            x += 1;
            x -= 1;
            print(&x);
        }
        '''
        , err_test=False)

    def test_v1(self):
        self.runNcmp(
        '''
        int test(int a, int b, char c) {
            int i = 0 - 14/3 + (2*34 + 13 +(-4));
            return i;
        }
        '''
        , err_test=False)

    def test_v2(self):
        self.runNcmp(
        '''
        int test(int a, int b, char c) {
            int i = 12;
            float f = (float)i;
            return i;
        }
        '''
        , err_test=False)

    def test_v3(self):
        self.runNcmp(
        '''
        int test(int a, int b, char c) {
            float f = 12.5;
            int i = (int)f;
            return i;
        }
        '''
        , err_test=False)

    def test_v4(self):
        self.runNcmp(
        '''
        int test(int a, int b, char c) {
            return a+b+c;
        }
        '''
        , err_test=True)
    
    def test_v5(self):
        self.runNcmp(
        '''
        int test(int a, int b, char c) {
            return a+b;
        }
        '''
        , err_test=False)

    def test_v6(self):
        self.runNcmp(
        '''
        int i = 0;

        int test(int a, int b, char c) {
            int i = 1;
            return i;
        }
        '''
        , err_test=False)

    def test_v7(self):
        self.runNcmp(
        '''
        int i = 0;

        int test(int a, int b, char c) {
            int i = 1;
            return i;
        }

        int i;
        '''
        , err_test=True)

    def test_v8(self):
        self.runNcmp(
        '''
        int i = 2.31;
        
        void main ( ) {
            ++i;
            i++;
            return;
        }
        '''
        , err_test=True)

    def test_v9(self):
        self.runNcmp(
        '''
        int i = 2.31;
        
        '''
        , err_test=True)

    # Arrays

    def test_a1(self):
        self.runNcmp(
        '''
        int i[] = {1,2,3,4};
        float f[2] = {.1, .2};
        
        // Strings
        char s[10];
        char s1[] = "Hello World!";
        char str[10] = "some/path";
        char str1[3] = "abc";
        char str2[3] = {'a','b','c'};

        int a = i[1] + i[3];
        float b = f[1]*f[0];
        char c = str2[3];
        '''
        , err_test=False)

    def test_a2(self):
        self.runNcmp(
        '''
        int i[];
        '''
        , err_test=True)




        

if __name__ == '__main__':
    unittest.main()
