from loki import *
import sys
sys.path.append("../..")
from scc_lint import * 
test_path=""

map_check = { 
    1: check1,
    2: check2,
    3: check3,
    4: check4,
    5: check5,
    6: check6,
    7: check7,
    8: check8,
    9: check9,
    10: check10,
    11: check11,
 #    12: check12,
    13: check13,
    14: check14
    }
def open(sub, tes_path=""):
    file=test_path+sub
    s=Sourcefile.from_file(file)
    subroutine=s.subroutines[0]
    return(subroutine)


verbose = True
def test_(n, result):
    subroutine=open(f"sub{n}.F90", test_path)
    check=map_check[n]
#    resolve_associates(subroutine)
    if verbose: print(f"======== test {n} ======")
    if verbose: print(repr(check(subroutine)))
    #if verbose: print(check(subroutine))
    if result != "": assert check(subroutine)==result
    if verbose: print(f"====== end test {n} ======")
   

result1="Routine :  SUB1 => 1 dummy args allocatable : ['B'] \nRoutine :  SUB1 => 1 dummy args pointer : ['A']"
test_(1, result1)
result2="Routine :  SUB2 => 1 dummy args with no intent : ['A']"
test_(2, result2)
result3="Routine :  SUB3 => 1 dummy args with assumed shapes: ['A']"
test_(3, result3)
result4="Routine :  SUB4 => ydmodel has wrong intent : inout (not intent in) \nRoutine :  SUB4 => ydgeometry has wrong intent : out (not intent in) \n"
test_(4, result4)
result5="Routine :  SUB5 => 4 temp with leading dim diff than nproma: ['B', 'C', 'C', 'D']"
test_(5, result5)
