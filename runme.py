import os

if __name__ == "__main__":
    for n in range(1, 16 + 1):
        print(f"== {n} ==")
        os.system(f"python uC.py -s -o -l tests\\project-4\\t{n}.uc")
    print(f"== end ==")