import os
import sys


if len(sys.argv) > 1 and sys.argv[1] == "clean":
    for fname, ext in [f.split('.') for f in os.listdir("uc")]:
        if ext == "ast":
            os.system(f"rm uc/{fname}.{ext}")
            print(f"CLEAN: uc/{fname}.{ext}")

else:
    executable = "../../uC.py"

    for fname, ext in [f.split('.') for f in os.listdir("uc")]:
        if ext == "uc":
            os.system(f"python {executable} uc/{fname}.{ext}")

    for fname, _ in [f.split('.') for f in os.listdir("ast")]:
        ret = os.system(f"diff -u uc/{fname}.ast ast/{fname}.ast > diff/{fname}.diff")
        if ret != 0:
            print(f"DIFF: {fname}.diff")