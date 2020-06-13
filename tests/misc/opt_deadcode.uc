int global;

void f() {
    int i;
    i = 1;          /* dead store */
    global = 1;     /* dead store */
    global = 2;
    return;
    global = 3;     /* unreachable */
}

void main() {} /* uncomment to use without -no-run */

/** Below is the code fragment after dead code elimination:
 *
 *  int global;
 *  void f() {
 *    global = 2;
 *    return;
 *  }
 *
 */