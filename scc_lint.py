"""
Args NPROMA routines : 
ARRAYS ::: REAL, INTEGER, LOGICAL + intent attribute
YDMODEL YDGEOMETRY => INTENT(IN)
YDVARS => INTENT(IN) 

assumed shape forbidden
f77 implied shape arrays 
Dummy # ALLOCATABLE or POINTER attribute
"""

from loki import *


s=Sourcefile.from_file("sub.F90")
routine=s["SUB"]

#=====================================================================
#=====================================================================
#                 Dummy arguments of NPROMA routines
#=====================================================================
#=====================================================================
def check1(routine):
    """
    Checks if some dummy args are ALLOCATABLE or POINTER. 
    """
    dummy_args=[var for var in routine.variables if var in routine.arguments]
    lst_alloc=[var.name for var in dummy_args if var.type.allocatable]
    lst_pointer=[var.name for var in dummy_args if var.type.pointer]
   
    result=""
    if lst_alloc:
        result=f"Routine :  {routine.name} => {len(lst_alloc)} dummy args allocatable : {lst_alloc} \n" 
    if lst_pointer:
        result+=f"Routine :  {routine.name} => {len(lst_pointer)} dummy args pointer : {lst_pointer}"
    if len(result)!=0:
        return(result)

def check2(routine):
    """
    Checks if some dummy args have no INTENT.
    """
    lst_no_intent=[var.name for var in routine.arguments if not var.type.intent]
    if lst_no_intent:
        result=f"Routine :  {routine.name} => {len(lst_no_intent)} dummy args with no intent : {lst_no_intent}"
    if result:
        return(result)
def check3(routine):
    """
    Checks if some dummy args assumed shapes.
    """
    def is_assume(shapes):
        if shapes:
            for shape in shapes:
                if type(shape)==RangeIndex:
                    return(True)
            return(False)
    lst_assume_shape=[var.name for var in routine.variables if (is_assume(var.type.shape))]
    if lst_assume_shape:
        result=f"Routine :  {routine.name} => {len(lst_assume_shape)} dummy args with assumed shapes: {lst_assume_shape}"
    if result:
        return(result)

def check4(routine):
    """
    Checks if YDMODEL, YDGEOMETRY have the INTENT(IN) attribute.
    """
    result=""
    for variable_name in ["ydmodel", "ydgeometry"]:
    #for variable_name in ["ydmodel", "ydgeometry", "ydvars"]:
        if variable_name in routine.variable_map:
            variable=routine.variable_map[variable_name]
            if not variable.type.intent:
                result+=f"Routine :  {routine.name} => {variable_name} has no intent \n"

            else:
                if variable.type.intent!="in":
      
                    result+=f"Routine :  {routine.name} => {variable_name} has wrong intent : {variable.type.intent} (not intent in) \n" 

    if(len(result)!=0):
        return(result)
#=====================================================================
#=====================================================================
#                 Temporaries of NPROMA routines
#=====================================================================
#=====================================================================

def check5(routine):
    """
    Checks that NPROMA is the first dimension of temporaries, if not dim must be known at compile time.
    """
    lst_horizontal=["NPROMA", "KLON"]
    lst_not_nproma=[]
    temps=[var for var in routine.variables if var not in routine.arguments and isinstance(var, Array)]
   
    for var in temps:
        if type(var.shape[0])==DeferredTypeSymbol: 
            if var.shape[0] not in lst_horizontal:
                lst_not_nproma.append(var.name)    
    if len(lst_not_nproma)!=0:
        result=f"Routine :  {routine.name} => {len(lst_not_nproma)} temp with leading diff than nproma: {lst_not_nproma}"
        return(result)   
def check6(routine):
    """
    Checks if temporaries aren't ALLOCATABLE 
    """
    temps=[var for var in routine.variables if var not in routine.arguments and isinstance(var, Array)]
   
    lst_alloc=[var.name for var in temps if var.type.allocatable]
    result=""
    if lst_alloc:
        result=f"Routine :  {routine.name} => {len(lst_alloc)} temp allocatable : {lst_alloc}" 
    if len(result)!=0:
        return(result)
     
#Dummy arguments of NPROMA routines ::: 
print(check1(routine))
print(check2(routine))
print(check3(routine))
print(check4(routine))
#Temporaries of NPROMA routines 
print(check5(routine))
print(check6(routine))
