int main() {
    int x = 14;
    int y = 7 - x / 2;
    return y * (28 / x + 2);
}

/** Below is the code fragment after constant propagation and constant folding,
 *  which could be further optimized by dead code elimination of both x and y:
 *
 *  int main() {
 *    int x = 14;
 *    int y = 0;
 *    return 0;
 *  }
 *
 */