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
import sys
import copy


is_index=False #if no index, YDVARS%VAR1%VAR2 is unkown
is_index=True #if there is an index, YDVARS%VAR1%VAR2 is known
debug=False
if debug:
    s=Sourcefile.from_file("sub.F90")
    subroutine=s["SUB"]
else:
    file=sys.argv[1]
    s=Sourcefile.from_file(file)
    subroutine=s.subroutines[0]
    resolve_associates(subroutine)
#    print(fgen(subroutine.body))

import inspect
verbose=False


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
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
    if len(msg)!=0:
        return(msg)
    
def check2(subroutine):
    """
    Checks if some dummy args have no INTENT.
    """
    msg=""
    lst_no_intent=[var.name for var in subroutine.arguments if not var.type.intent]
    if lst_no_intent:
        msg=f"Routine :  {subroutine.name} => {len(lst_no_intent)} dummy args with no intent : {lst_no_intent}"
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
    if len(msg)!=0:
        return(msg)
def check3(subroutine):
    """
    Checks if some dummy args assumed shapes.
    """
    msg=""
    def is_assume(shapes):
        if shapes:
            for shape in shapes:
                if type(shape)==RangeIndex:
                    if (not any(shape.children)):
                        return(True)
            return(False)
    lst_assume_shape=[var.name for var in subroutine.variables if (is_assume(var.type.shape) and not var.type.pointer)]
    if lst_assume_shape:
        msg=f"Routine :  {subroutine.name} => {len(lst_assume_shape)} dummy args with assumed shapes: {lst_assume_shape}"
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
    if len(msg)!=0:
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
    
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
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
    NPROMA=["NPROMA", "KLON","YDGEOMETRY%YRDIM%NPROMA","YDCPG_OPTS%KLON","D%NIJT","KPROMA"]
    lst_not_nproma=[]
    temps=[var for var in subroutine.variables if var not in subroutine.arguments and isinstance(var, Array)]
    
    for var in temps:
        if type(var.shape[0])==DeferredTypeSymbol: 
            if var.shape[0] not in NPROMA:
            #if var.shape[0] not in lst_horizontal:
                    lst_not_nproma.append(var.name)    
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
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
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
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
            if var.type.pointer:
                pt_asss.append(ass)
                break
       
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
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
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
    ignore_calls=['NEW_ADD_FIELD_3D','DR_HOOK','ADD_FIELD_3D']
    #verbose=True
    verbose=False
#    exception="PXSL"
#    exceptions=[exception]
    calls=FindNodes(CallStatement).visit(subroutine.body)
    c_import=[imp.module.replace('.intfb.h','') for imp in FindNodes(Import).visit(subroutine.spec) if imp.c_import]
    new_calls=copy.deepcopy(calls)
    for call in calls:
        if call in new_calls:
            if call.name.name.lower() in c_import:
                new_calls.remove(call)
    new_calls=[call.name.name for call in new_calls]
    new_calls=[call for call in new_calls if call not in ignore_calls]
    #new_calls=[call for call in new_calls if call!='DR_HOOK']
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
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
                elif (isinstance(dim, IntLiteral) or isinstance(dim, DeferredTypeSymbol) or isinstance(dim, Scalar)): 
                
                    is_scalar=True
                else:
                    print("arg = ", arg)
                    print("dim =", dim)
                    raise NotImplementedError(f"dim is neither slice, section or scalar : dim = {dim}")
                
        if msg_call:
            msg+=f" *** Call : {call.name.name} => " + msg_call + "\n" 

    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
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
    lst_import=['GEOMETRY', 'MF_PHYS_TYPE', 'CPG_MISC_TYPE', 'CPG_DYN_TYPE', 'CPG_GPAR_TYPE', 'CPG_PHY_TYPE', 'CPG_SL2_TYPE', 'CPG_BNDS_TYPE', 'CPG_OPTS_TYPE', 'MF_PHYS_SURF_TYPE', 'FIELD_VARIABLES', 'MF_PHYS_BASE_STATE_TYPE', 'MF_PHYS_NEXT_STATE_TYPE', 'MODEL', 'JPIM', 'JPRB', 'LHOOK', 'DR_HOOK', 'JPHOOK', 'TYP_DDH','JPRD','NEW_ADD_FIELD_3D','ADD_FIELD_3D']
    
    module_vars=[]
    imports=FindNodes(Import).visit(subroutine.spec) 
    for imp in imports:
        if imp.symbols:
            for symbol in imp.symbols:
                if symbol not in lst_import:
                    if not (re.match(r'^T', symbol.name) or re.search(r'TYPE$', symbol.name)):
                        if symbol.name not in ['LFLEXDIA','LMUSCLFA','NMUSCLFA']:
                            module_vars.append(symbol.name)
                            
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
    if len(module_vars) !=0:
        return(f"Routine :  {subroutine.name} => module variables : {module_vars} are forbidden")
#=====================================================================
#=====================================================================
#                 Modules variables in NPROMA routines
#=====================================================================
#=====================================================================
def check11(subroutine):
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
                    #if dim == ':':
                    if isinstance(dim, RangeIndex):
                        #if not any(dim.children): # ':'
                        is_array_syntax=True
                            

        if isinstance(assign.rhs, Array):
            is_copy=True
        if (isinstance(assign.rhs, FloatLiteral) or isinstance(assign.rhs, IntLiteral) or isinstance(assign.rhs, LogicLiteral)):
#        if not FindVariables().visit(assign.rhs):
            is_init=True
#todo if rhs is a big expression of constants 
        if (isinstance(assign.rhs, Product)):
            if assign.rhs.children[0]==-1 and isinstance(assign.rhs.children[1], FloatLiteral):
                is_init=True
    
        if (is_array_syntax and not is_copy) and (is_array_syntax and not is_init):
            msg+=f" *** Some array syntax in {fgen(assign)}\n"
     
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
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
#    if opt:
#        lst_no_import=[]
#        c_import=[for imp in FindNodes(Import).visit(subroutine.spec) if imp.c_import]
#        for func in lst_func:
#            if func not in c_import:
#                lst_no_import.append(func)
#            else:
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
    if len(lst_func)!=0:
        return(f"Routine :  {subroutine.name} => {lst_func} are function calls.")
#=====================================================================
#=====================================================================
#                Notations in NPROMA routines 
#=====================================================================
#=====================================================================
def check14(subroutine):
    """
    Checks if horizontal dimension, horizontal bounds and horizontal index have the right name.
    names in NPROMA, BOUNDS and JLON.
    """
    NPROMA=["NPROMA", "KLON","YDGEOMETRY%YRDIM%NPROMA","YDCPG_OPTS%KLON","D%NIJT","KPROMA"]
    BOUNDS=["KST/KEND","KIDIA/KFDIA","YDCPG_BNDS%KIDIA/KDCPG_BNDS%KFDIA","D%NIJB/D%NIJE","D%NIB/D%NIE"]
    JLON=["JLON","JROF","JIJ","JI"]

    msg=""
    msg_nproma=""
    verbose=False
#    verbose=True

    lst_not_nproma=[]
#    arrays=[var for var in subroutine.variables if var not in subroutine.arguments and isinstance(var, Array)]
   
#1- first check that first dim of arrays in NPROMA
#!!!! CAN BE NONE NPROMA ARRAYS IN YDVARS ?? !!!!!
    #OR DIRECTLY CALL CHECK5
    arrays=[var for var in FindVariables().visit(subroutine.body) if isinstance(var, Array)]
    for var in arrays:
        if var.shape:
            if type(var.shape[0])==(DeferredTypeSymbol or Scalar): 
                if var.shape[0].name not in NPROMA:
                    if verbose: msg_nproma+=f" *** var : {var.name} has none nproma dim as first dim : {var.shape[0].name}\n"
                    
                    lst_not_nproma.append(var.name)    
            else:
                lst_not_nproma.append(var.name)    
                if verbose: msg_nproma+=f" *** var : {var.name} has range indx first dim !!! \n"
        else:
            #derived type will arrive here : TODO ::: add the index with the derived types.
            lst_not_nproma.append(var.name) 
            if verbose: msg_nproma+=f" *** var : {var.name} has unknow first dim !!! \n"
    if len(msg_nproma)!=0:
        print(msg_nproma) 
    #if verbose: print(msg_nproma) 
#2- Then insect each loop 
    
    loops=[loop for loop in FindNodes(Loop).visit(subroutine.body)]
    for loop in loops:
        #is_int=False 
        msg_loop=""
        
#        print("loop = ", loop)
#        print("loop_bounds = ", loop.bounds)
        #Lower bound
#        if isinstance(loop.bounds.lower, IntLiteral):
#            #is_int=True
#            loop_bounds=str(loop.bounds.lower.value)
#        if isinstance(loop.bounds.lower, DeferredTypeSymbol):    
#            loop_bounds=loop.bounds.lower.name
#        if isinstance(loop.bounds.lower, Scalar):    
#            loop_bounds=loop.bounds.lower.name
#        #Upper bound
#        if isinstance(loop.bounds.upper, IntLiteral):
#            #is_int=True
#            loop_bounds=loop_bounds+"/"+str(loop.bounds.upper.value)
#        if isinstance(loop.bounds.upper, DeferredTypeSymbol):    
#            loop_bounds=loop_bounds+"/"+loop.bounds.upper.name
#        if isinstance(loop.bounds.upper, Scalar):    
#            loop_bounds=loop.bounds.upper.name

        loop_bounds=str(loop.bounds.lower)+'/'+str(loop.bounds.upper)

        
        loop_idx=loop.variable
       # if loop_bounds not in 
        loop_vars1=FindVariables().visit(loop.body)
        loop_vars=[var for var in loop_vars1 if isinstance(var, Array)]       
        is_bound=loop_bounds in BOUNDS
        is_idx=loop_idx.name in JLON

        for var in loop_vars:
            if var.name not in lst_not_nproma:
                if var.dimensions[0] != loop_idx: #isn't loop over the first dim. And that means not a nproma loop if 1- is True      
                    break
                else: #first dimension is the loop idx
                    is_nproma=var.shape[0].name in NPROMA

                    is_bound=True
                if not is_idx:
                    msg_loop+=f"wrong loop variable : {loop_idx.name}; "
                    is_idx=True
                if not is_nproma:
                    msg_loop+=f"var : {var.name} has unknwown first dimension : {var.shape[0].name}; "
        if len(msg_loop)!=0:
            msg+=f" *** loop : {loop} => {msg_loop} \n"
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
    if len(msg)!=0:
        return(f"Routine :  {subroutine.name} => \n {msg}")
        
#=====================================================================
#=====================================================================
#       Calling NPROMA routines from an OpenMP parallel section 
#=====================================================================
#=====================================================================

#ignore, just 4 places in the code with that

#=====================================================================
#=====================================================================
#                  Reductions in NPROMA routines
#=====================================================================
#=====================================================================

def check15(subroutine):
    
   """
   Check if MINVAL or MAXVAL are used. 
   SUM can be use, but the result of the sum musn't be used in a calculation, it will break reproductibility. 
   """
   calls=[]
#   lst_sum=[]
   msg=""
   for assign in FindNodes(Assignment).visit(subroutine.body):
       for call in FindInlineCalls().visit(assign):
#           if (call.name=="SUM"):
#               lst_sum.append(assign.lhs)
   
           if (call.name=="MINVAL") or (call.name=="MAXVAL"):
               msg+="*** " + fgen(assign)+"\n"
     
   frame = inspect.currentframe()
   if verbose: print("The name of function is : ", frame.f_code.co_name)
   if len(msg)!=0:
       return(f"Routine :  {subroutine.name} => Some reductions were detected : \n {msg}")
#=====================================================================
#=====================================================================
#       Gather/scatter (aka pack/unpack) in NPROMA routines 
#=====================================================================
#=====================================================================

def check16(subroutine):
    """
    In order to check if gather scatter is used, we check if indirect addressing is used
    """
    msg=""
    for var in FindVariables().visit(subroutine.body):
        if isinstance(var, Array):

            is_array=var.name_parts[0] in subroutine.variable_map #don't take functions 
            
            if is_array:
                for dim in var.dimensions:
                    if isinstance(dim, Array):
                        msg+=f"*** {fgen(var)}; "
                    break
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
    if(len(msg))!=0:
        return(f"Routine :  {subroutine.name} => Some indirect addressing was detected: \n {msg}")

#=====================================================================
#=====================================================================
#               Directives in NPROMA routines 
#=====================================================================
#=====================================================================

    
def show(routine, subroutine):
    c=routine(subroutine)
    if c:
        print(c)

       
#Dummy arguments of NPROMA subroutines ::: 
show(check1,subroutine)
show(check2,subroutine)
show(check3,subroutine)
show(check4,subroutine)
#Temporaries of NPROMA subroutines 
show(check5,subroutine)
show(check6,subroutine)
#Pointers in NPROMA routines 
show(check7,subroutine)
#Calling other NPROMA routines 
show(check8,subroutine)
show(check9,subroutine)
#Modules variables in NPROMA routines
show(check10,subroutine)
#Calculations in NPROMA routines
show(check11,subroutine)
#show(check12,subroutine)
#Functions in NPROMA routines
show(check13,subroutine)
#Notations in NPROMA routines
show(check14,subroutine)
#Calling NPROMA routines from an OpenMP parallel section 
#skip
#Reductions in NPROMA routines
show(check15,subroutine)
#Gather/scatter (aka pack/unpack) in NPROMA routines
show(check16,subroutine)
