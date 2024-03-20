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

import re

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
#=====================================================================
#=====================================================================
#                Pointers in NPROMA routines 
#=====================================================================
#=====================================================================

def check7(subroutine):
    """
    Pointers are forbidden, except for handling optional arguments. For instance : 
    """
    verbose=False
    #verbose=True
    temps=[var for var in subroutine.variables if var not in subroutine.arguments and isinstance(var, Array)]
    pt=[var for var in temps if var.type.pointer]
    pt_name=[var.name for var in temps if var.type.pointer]
    asss=FindNodes(Assignment).visit(subroutine.body) #when pt assignment found in an IF(PRESENT), rm the ass for the list. At the end, look for pt assignment in the list :  1)If the list is empty, that means that pointers were used where they are allowed to be used. 2)Else, rule not respected
    pt_asss=[]
    for ass in asss:
        for var in FindVariables(Array).visit(ass):
            if verbose: print("var=", var)
            if verbose: print("ass=", ass)
            if var.type.pointer:
                pt_asss.append(ass)
                break
       
    if verbose: print("pt_asss=", pt_asss)
    conds=FindNodes(Conditional).visit(subroutine.body)
    for cond in conds:
        calls=FindInlineCalls().visit(cond.condition)
        calls=[call for call in calls if call.name=="PRESENT"]
        if calls:
            cond_asss=FindNodes(Assignment).visit(cond)
           # is_pt=True #check is lhs = PT in both IF and ELSE blk
            for cond_ass in cond_asss:
                if cond_ass.lhs.name in pt_name: #and is_pt:
                    pt_asss.remove(cond_ass)
                    is_pt=True
            #    else:
            #        is_pt=False
                     
    
    pointers=[]
    for ass in pt_asss:
        variables=FindVariables(Array).visit(ass)
        for var in variables:
            if var.type.pointer:
                pointers.append(var.name)
    if pt_asss:
        msg=f"Routine :  {subroutine.name} => wrong use of some pointers : {pointers}"
        return(msg)
#=====================================================================
#=====================================================================
#                   Calling other NPROMA routines 
#=====================================================================
#=====================================================================
   
def check8(subroutine):
    """
    Checks if all routines call from the NPROMA routine are declared using an interface block.
    """
    verbose=True
#    exception="PXSL"
#    exceptions=[exception]
    calls=FindNodes(CallStatement).visit(subroutine.body)
    c_import=[imp.module.replace('.intfb.h','') for imp in FindNodes(Import).visit(subroutine.spec) if imp.c_import]
    new_calls=calls
    if verbose: print("calls = ", calls)
    if verbose: print("c_import = ", c_import)
    for call in calls:
        if call in calls:
            if call.name.name.lower() in c_import:
                new_calls.remove(call)
    new_calls=[call.name.name for call in new_calls]
    if new_calls:
        msg=f"Routine :  {subroutine.name} => some subroutines call from the subroutine aren't declared using an interface block : {new_calls}"
        return(msg)

def check9(subroutine):
    """
    Checks if array sections passed to NPROMA routines use the Fortran slice notation.
    This shouldn't be use outside NPROMA routines. Outside NPROMA routines, some non-NPROMA routines can be called. Todo : add smthg if this check is used in a driver routine.

    CALL( ... Array\((:,)*(X:Y){0,1}(N)*\) ... )
    : => is_slice = True
    X:Y => is_section = True
    N => is_scalar = True
    """
    msg=""
    calls=FindNodes(CallStatement).visit(subroutine.body)
    for call in calls:
        args=[arg for arg in call.arguments if isinstance(arg, Array)]
        msg_call=""
        for arg in args:
            is_slice=False
            is_section=False
            is_scalar=False
            
            dims=arg.dimensions
            for dim in dims:
                if isinstance(dim, RangeIndex):
                    if is_scalar: #scalar before ':' or 'X:Y'
                        msg_call+=f"Array not contiguous : array {arg.name}; "
                    if not any(dim.children): # ':'
                        if is_section: # 'X:Y' before ':'
                            msg_call+=f"Section before a slice forbidden : array {arg.name}; "
                        is_slice=True
                    else: # 'X:Y' 
                        if dim.children[2]:
                            msg_call+=f"Stride are forbidden : array {arg.name}; " #{dim.children}; "
                        else:
                            if is_section:
                                msg_call+=f"Two slices for the same array are forbidden : array {arg.name}; "
                            is_section=True
                elif isinstance(dim, IntLiteral) or isinstance(dim, DeferredTypeSymbol): 
                
                    is_scalar=True
                else:
                    raise NotImplementedError(f"dim is neither slice, section or scalar : dim = {dim}")
                
        if msg_call:
            msg+=f" *** Call : {call.name.name} => " + msg_call + "\n" 

    if len(msg)!=0:
        return(f"Routine :  {subroutine.name} => \n" + msg)
#=====================================================================
#=====================================================================
#                 Modules variables in NPROMA routines
#=====================================================================
#=====================================================================
def check10(subroutine):
    """
    Checks if modules variables are used.
    Are allowed: modules variables in lst_import + ['LFLEXDIA','LMUSCLFA','NMUSCLFA'] + var starting with T or ending with TYPE, that is module var that are TYPES
    """
    verbose=False
    lst_import=['GEOMETRY', 'MF_PHYS_TYPE', 'CPG_MISC_TYPE', 'CPG_DYN_TYPE', 'CPG_GPAR_TYPE', 'CPG_PHY_TYPE', 'CPG_SL2_TYPE', 'CPG_BNDS_TYPE', 'CPG_OPTS_TYPE', 'MF_PHYS_SURF_TYPE', 'FIELD_VARIABLES', 'MF_PHYS_BASE_STATE_TYPE', 'MF_PHYS_NEXT_STATE_TYPE', 'MODEL', 'JPIM', 'JPRB', 'LHOOK', 'DR_HOOK', 'JPHOOK', 'TYP_DDH']
    
    module_vars=[]
    imports=FindNodes(Import).visit(subroutine.spec) 
    for imp in imports:
        if imp.symbols:
            for symbol in imp.symbols:
                if verbose: print(symbol)
                if symbol not in lst_import:
                    if not (re.match(r'^T', symbol.name) or re.search(r'TYPE$', symbol.name)):
                        if symbol.name not in ['LFLEXDIA','LMUSCLFA','NMUSCLFA']:
                            module_vars.append(symbol.name)
                            
    if len(module_vars) !=0:
        return(f"Routine :  {subroutine.name} => module variables : {module_vars} are forbidden")
#=====================================================================
#=====================================================================
#                 Modules variables in NPROMA routines
#=====================================================================
#=====================================================================
def check11(subrouine):
    """
    Array syntax is forbidden, except for array initialization and array copy.
    """               
    verbose=False
    msg=""
    for assign in FindNodes(Assignment).visit(subroutine.body):
        is_copy=False
        is_init=False
        is_array_syntax=False
        for var in FindVariables().visit(assign.lhs):
            if isinstance(var, Array):
                for dim in var.dimensions:
                    if dim == ':':
                        is_array_syntax=True
        if isinstance(assign.rhs, Array):
            is_copy=True
        if not FindVariables().visit(assign.rhs):
            is_init=True
    
        if verbose: print(assign, is_array_syntax and not is_copy)
        if verbose: print(assign, is_array_syntax and not is_init)
        if (is_array_syntax and not is_copy) and (is_array_syntax and not is_init):
            msg+=f" *** Some array syntax in {fgen(assign)}\n"
     
    if len(msg)!=0:
        return(f"Routine :  {subroutine.name} => " + '\n' + msg)
        
#def check12(subroutine):
#TODO : check if constants init are done at the begining of the routine

#=====================================================================
#=====================================================================
#                Functions in NPROMA routines
#=====================================================================
#=====================================================================
def check13(subroutine):
    """
    Check if functions that aren't statement functions are used. 
    """
#
#A(...) =>  
#    IF 1) A is an array declared in the routine; 2) member of a derived type; 3) starts with f : statement functions
#    ELSE  A is a function => forbidden!
# Optional :  Check for function if intfb.h; check for func.h

    lst_func=[]
    lst_statement_func=[]
    variables=[var for var in FindVariables().visit(subroutine.body)]
    for var in variables:
        if isinstance(var, Array):
            is_array=var.name in subroutine.variable_map
            is_derived_type='%' in var.name
            is_statement_func=(re.match(r'^F', var.name))
            if is_statement_func:
                if not var.name in lst_statement_func:
                    lst_statement_func.append(var.name)
            if (not is_array) and (not is_derived_type) and (not is_statement_func):
                if not var.name in lst_func:
                    lst_func.append(var.name)
    if len(lst_func)!=0:
        return(f"Routine :  {subroutine.name} => {lst_func} are function calls.")
                
                
            

#=====================================================================
#=====================================================================
#                Notations in NPROMA routines 
#=====================================================================
#=====================================================================


#Dummy arguments of NPROMA subroutines ::: 
print(check1(subroutine))
print(check2(subroutine))
print(check3(subroutine))
print(check4(subroutine))
#Temporaries of NPROMA subroutines 
print(check5(subroutine))
print(check6(subroutine))
#Pointers in NPROMA routines 
print(check7(subroutine))
#Calling other NPROMA routines 
print(check8(subroutine))
print(check9(subroutine))
#Modules variables in NPROMA routines
print(check10(subroutine))
#Calculations in NPROMA routines
print(check11(subroutine))
#print((check12(subroutine))
#Functions in NPROMA routines
print(check13(subroutine))

