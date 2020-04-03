import os
import sys

for fname, ext in [f.split('.') for f in os.listdir("uc")]:
    if ext == "uc":
        os.system(f"python ../uC.py uc/{fname}.{ext}")

for fname, _ in [f.split('.') for f in os.listdir("ast")]:
    ret = os.system(f"diff -u uc/{fname}.ast ast/{fname}.ast > diff/{fname}.diff")
    if ret != 0:
        print(f"DIFF: {fname}.diff")