"""
Args NPROMA subroutines : 
ARRAYS ::: REAL, INTEGER, LOGICAL + intent attribute
YDMODEL YDGEOMETRY => INTENT(IN)
YDVARS => INTENT(IN) 

assumed shape forbidden
f77 implied shape arrays 
Dummy # ALLOCATABLE or POINTER attribute
"""

from loki import *


s=Sourcefile.from_file("sub.F90")
subroutine=s["SUB"]

#=====================================================================
#=====================================================================
#                 Dummy arguments of NPROMA subroutines
#=====================================================================
#=====================================================================
def check1(subroutine):
    """
    Checks if some dummy args are ALLOCATABLE or POINTER. 
    """
    dummy_args=[var for var in subroutine.variables if var in subroutine.arguments]
    lst_alloc=[var.name for var in dummy_args if var.type.allocatable]
    lst_pointer=[var.name for var in dummy_args if var.type.pointer]
   
    msg=""
    if lst_alloc:
        msg=f"Routine :  {subroutine.name} => {len(lst_alloc)} dummy args allocatable : {lst_alloc} \n" 
    if lst_pointer:
        msg+=f"Routine :  {subroutine.name} => {len(lst_pointer)} dummy args pointer : {lst_pointer}"
    if len(msg)!=0:
        return(msg)

def check2(subroutine):
    """
    Checks if some dummy args have no INTENT.
    """
    lst_no_intent=[var.name for var in subroutine.arguments if not var.type.intent]
    if lst_no_intent:
        msg=f"Routine :  {subroutine.name} => {len(lst_no_intent)} dummy args with no intent : {lst_no_intent}"
    if msg:
        return(msg)
def check3(subroutine):
    """
    Checks if some dummy args assumed shapes.
    """
    def is_assume(shapes):
        if shapes:
            for shape in shapes:
                if type(shape)==RangeIndex:
                    return(True)
            return(False)
    lst_assume_shape=[var.name for var in subroutine.variables if (is_assume(var.type.shape))]
    if lst_assume_shape:
        msg=f"Routine :  {subroutine.name} => {len(lst_assume_shape)} dummy args with assumed shapes: {lst_assume_shape}"
    if msg:
        return(msg)

def check4(subroutine):
    """
    Checks if YDMODEL, YDGEOMETRY have the INTENT(IN) attribute.
    """
    msg=""
    for variable_name in ["ydmodel", "ydgeometry"]:
    #for variable_name in ["ydmodel", "ydgeometry", "ydvars"]:
        if variable_name in subroutine.variable_map:
            variable=subroutine.variable_map[variable_name]
            if not variable.type.intent:
                msg+=f"Routine :  {subroutine.name} => {variable_name} has no intent \n"

            else:
                if variable.type.intent!="in":
      
                    msg+=f"Routine :  {subroutine.name} => {variable_name} has wrong intent : {variable.type.intent} (not intent in) \n" 

    if(len(msg)!=0):
        return(msg)
#=====================================================================
#=====================================================================
#                 Temporaries of NPROMA subroutines
#=====================================================================
#=====================================================================

def check5(subroutine):
    """
    Checks that NPROMA is the first dimension of temporaries, if not dim must be known at compile time.
    """
    lst_horizontal=["NPROMA", "KLON"]
    lst_not_nproma=[]
    temps=[var for var in subroutine.variables if var not in subroutine.arguments and isinstance(var, Array)]
   
    for var in temps:
        if type(var.shape[0])==DeferredTypeSymbol: 
            if var.shape[0] not in lst_horizontal:
                lst_not_nproma.append(var.name)    
    if len(lst_not_nproma)!=0:
        msg=f"Routine :  {subroutine.name} => {len(lst_not_nproma)} temp with leading diff than nproma: {lst_not_nproma}"
        return(msg)   
def check6(subroutine):
    """
    Checks if temporaries aren't ALLOCATABLE 
    """
    temps=[var for var in subroutine.variables if var not in subroutine.arguments and isinstance(var, Array)]
   
    lst_alloc=[var.name for var in temps if var.type.allocatable]
    msg=""
    if lst_alloc:
        msg=f"Routine :  {subroutine.name} => {len(lst_alloc)} temp allocatable : {lst_alloc}" 
    if len(msg)!=0:
        return(msg)
     
#Dummy arguments of NPROMA subroutines ::: 
print(check1(subroutine))
print(check2(subroutine))
print(check3(subroutine))
print(check4(subroutine))
#Temporaries of NPROMA subroutines 
print(check5(subroutine))
print(check6(subroutine))
