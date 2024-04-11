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
#is_index=True #if there is an index, YDVARS%VAR1%VAR2 is known
debug=False


import inspect
verbose=False

def is_derive(var):
#    if isinstance(var, DeferredTypeSymbol):
    if len(var.name_parts)>1:
        return(True)
    return(False)

def get_type(var):
    return(var.name_parts[0])
    #return([sub].variable_map[var.name[0])


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
    Checks if some dummy args (that aren't pointers) have assumed shapes.
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
    if var is a pointer : ignore first dim check.
    """
    NPROMA=["NPROMA", "KLON","YDGEOMETRY%YRDIM%NPROMA","YDCPG_OPTS%KLON","D%NIJT","KPROMA"]
    lst_not_nproma_=[]
    temps=[var for var in subroutine.variables if var not in subroutine.arguments and isinstance(var, Array)]
    
    for var in temps:
        if isinstance(var.shape[0], DeferredTypeSymbol) or isinstance(var.shape[0], Scalar):
            if var.shape[0].name not in NPROMA:
                lst_not_nproma_.append(var)    
        elif not isinstance(var.shape[0], IntLiteral): 
            lst_not_nproma_.append(var)    

    lst_not_nproma_pt=[var.name for var in lst_not_nproma_ if var.type.pointer]
    lst_not_nproma=[var.name for var in lst_not_nproma_ if not var.type.pointer]
    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
    if len(lst_not_nproma)!=0:
        msg=f"Routine :  {subroutine.name} => {len(lst_not_nproma)} temp with leading dim diff than nproma: {lst_not_nproma}"
        if verbose: msg=msg + f"\n {len(lst_not_nproma_pt)} POINTERS temp with leading dim diff than nproma: {lst_not_proma_pt}"
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
    Pointers are forbidden, except: for handling optional arguments and if first dim isn't NPROMA.
    """
    verbose=False
    #verbose=True
    temps=[var for var in subroutine.variables if var not in subroutine.arguments and isinstance(var, Array)]
    pt=[var for var in temps if var.type.pointer]
    pt_name=[var.name for var in temps if var.type.pointer]
    asss=FindNodes(Assignment).visit(subroutine.body) #when pt assignment found in an IF(PRESENT), rm the ass for the list. At the end, look for pt assignment in the list :  1)If the list is empty, that means that pointers were used where they are allowed to be used. 2)Else, rule not respected
    pt_asss_derive=[]#assignment that can't be resolve because of derived type in them
    msg=""
    

    pt_asss=[ass for ass in FindNodes(Assignment).visit(subroutine.body) if ass.ptr]
    #derive_asss=[] #assignment that can't be resolve because of derived type in them

    def is_lst_pt(lst_pt, pt_asss,pt_cond_asss_bod,pt_cond_asss_else=None):
        """
        pt_cond_asss_body: pt assignment of the body of the cond
        pt_cond_asss_else: pt assignment of the else of the cond
        lst_pt: lst of 'PRESENT' vars
        pt_asss : all the pt assignment of the routine
    
        This routine checks if all the pointers assignment of at least the body or the else are all in the PRESENT clause. If it's the case, all the  pt assignments of the conditionnal are remove from the     routine pt_asss list.


        TARGET, OPTIONAL :: rhs1(DIM1,...
        POINTER :: lhs1(:,...
        TARGET :: rhs2(DIM1,...

        IF PRESENT(rhs1) !rhs is TARGET
        lhs1 => rhs1
        ELSE
        lhs1 => rhs2
        """
    
        lst_lhs={} #dict lst_lhs[lhs.name]=rhs, common to IF and ELSE parts. Need to store rhs to check if dimensions are the same in IF and ELSE.
        #lst_lhs=[] #lst of pointers on the lhs, common to IF and ELSE parts.
        to_remove_body=[] #if rhs is in the 'PRESENT' list, this pointer assignment can be removed.
        to_remove_else=[]
        for cond_ass in pt_cond_asss_body:
            if cond_ass.rhs.name in lst_pt:
                to_remove_body.append(cond_ass)
                lst_lhs[cond_ass.lhs.name]=cond_ass.rhs
                #lst_lhs.append(cond_ass.lhs.name)
        
        
        if pt_cond_asss_else:
            for cond_ass in pt_cond_asss_else:
                if cond_ass.rhs.name in lst_pt:
                    to_remove_else.append(cond_ass)
                    #add cond_ass.lhs.name to lst_lhs only of rhs1 and rhs2 have the same dimensions!!! 
                    if not is_index:
                        if is_derive(cond_ass.rhs):
                            pt_asss_derive.append(cond_ass)
                            break
                        if is_derive(cond_ass.lhs):
                            pt_asss_derive.append(cond_ass)
                            break
                    if is_index:
                        raise NotImplementedError("looking for derived type shape in the index isn't implemented yet!")


                    if cond_ass.rhs.shape == lst_lhs[cond_ass.lhs.name].sape: # rhs2.shape == lst_lhs[lhs1.name].shape = rhs1.shape
                    #if cond_ass.rhs.dimensions == lst_lhs[cond_ass.lhs.name].dimensions: # rhs2.dimensions == lst_lhs[lhs1.name].dimensions = rhs1.dimensions
                 #       lst_lhs.append(cond_ass.lhs.name)
                        lst_lhs[cond_ass.lhs.name]=cond_ass.rhs
                    #lst_lhs.append(cond_ass.lhs.name)
        
        
        if to_remove_body==pt_cond_asss_body or to_remove_else==pt_cond_asss_else:
            to_remove=to_remove_body+to_remove_else
            for cond_ass in pt_cond_asss_bod+pt_cond_asss_else:
                if cond_ass.lhs.name in lst_lhs:
                    pt_asss.remove(cond_ass)
#            for cond_ass in to_remove:
#                pt_asss.remove(cond_ass)
        
    
    def inspect_present(presents, dict_present):
       for present in presents:
           if len(present.arguments)>1:
               raise NotImplementedError("present should have only one arg, not implemented")
               
           if ass.lhs.name in map_logical:
               map_logical[ass.lhs.name].append(present.arguments[0].name)
           else:
               map_logical[ass.lhs.name]=[]
               map_logical[ass.lhs.name].append(present.arguments[0].name)
   
#1) look for VAR = smthg(PRESENT)
    map_logical={} #LOGICAL : all PRESENT vars
    asss=[ass for ass in FindNodes(Assignment).visit(subroutine.body)]

# TODO : don't just look for present but for PRESENT AND PRESENT...
    for ass in asss:
        calls=[call for call in FindInlineCalls().visit(ass)]
        presents=[call for call in calls if call.name=="PRESENT"]
        inspect_present(presents, map_logical)
        presents=[]
#2) look for cond IF ... PRESENT or IF(map_logical)


    conds=FindNodes(Conditional).visit(subroutine.body)
    for cond in conds:
          
        pt_cond_asss_body=[ass for ass in FindNodes(Assignment).visit(cond.body) if ass.ptr] 
        pt_cond_asss_else=[ass for ass in FindNodes(Assignment).visit(cond.else_body) if ass.ptr] 
        calls=FindInlineCalls().visit(cond.condition)
        if pt_cond_asss_body or pt_cond_asss_else: #if pt assignment in the cond body
            if calls: #IF( ... PRESENT)
                presents=[call for call in calls if call.name=="PRESENT"]
                for present in presents:
                    if len(present.arguments)>1:
                        raise NotImplementedError("present should have only one arg, not implemented")
                    lst_pt.append(present.arguments[0].name)
                
                is_lst_pt(lst_pt, pt_asss,pt_cond_asss_body,pt_cond_asss_else)
#                for cond_ass in pt_cond_asss:
#                    if cond_ass.lrs.name in lst_pt:
#                        pt_asss.remove(cond_ass)
            else: #IF(LTOTO) 
                if isinstance(cond.condition, Scalar):
                    if cond.condition.name in map_logical:
                        lst_pt=map_logical[cond.condition.name] #lst of pointers in the present clauses of the logical
        
                        is_lst_pt(lst_pt, pt_asss,pt_cond_asss_body,pt_cond_asss_else)
                       # for cond_ass in pt_cond_asss:
                       #     if cond_ass.rhs.name in lst_pt:
                       #         pt_asss.remove(cond_ass)
        lst_pt=[]
        presents=[]
        calls=[]
        pt_cond_asss_body=[]
        pt_cond_asss_else=[]


    NPROMA=["NPROMA", "KLON","YDGEOMETRY%YRDIM%NPROMA","YDCPG_OPTS%KLON","D%NIJT","KPROMA"]
#    new_pt_asss=copy.deepcopy(pt_asss)
#    for ass in pt_asss:
#==================================
# 1) '=>' is allowed if first dim isn't in NPROMA
# 2) If first dim is unknown : derive type; print message with ??? XX ???  
#==================================
    size_asss=len(pt_asss)
    idx_ass=0
    idx2=0
    while idx_ass<size_asss:
        ass=pt_asss[idx_ass+idx2]
        if ass.lhs.type.pointer:
            for var in FindVariables().visit(ass.rhs): 
                if is_derive(var):
                    if is_index:
                        #if is_derive(var):
                            #check if var.shape[0] in NPROMA, then remove (or not) ass from pt_asss
                        raise NotImplementedError("looking for derived type shape in the index isn't implemented yet!")
                    else:
                        #new_pt_asss.remove(ass)
                        idx2-=1
                        pt_asss.remove(ass)
                        pt_asss_derive.append(ass)    
                        break
                else: #if not derive type
                    if isinstance(var, Array):
                        if var.shape[0] not in NPROMA:
                            idx2-=1
                            pt_asss.remove(ass)
                            break
                    else:
                        if verbose: print("var = ", var, "isn't an array")
        idx_ass=idx_ass+1
    
#    pt_asss=copy.deepcopy(new_pt_asss)
    def get_pointers(pointers, asss):

        for ass in asss:
            variables=FindVariables(Array).visit(ass.lhs)
            for var in variables:
                if var.type.pointer:
                    pointers.append(var.name)
    pointers=[]
    get_pointers(pointers, pt_asss)
    if not is_index:
        pointers_derive=[]
        get_pointers(pointers_derive, pt_asss_derive)

    for ass in pt_asss_derive:
        variables=FindVariables(Array).visit(ass)
        for var in variables:
            if var.type.pointer:
                if isinstance(var.shape[0], DeferredTypeSymbol) or isinstance(var.shape[0], Scalar):
                    if var.shape[0] in NPROMA: #if first dim in NPROMA, pointer should respect what's tested above...
                        pointers.append(var.name)


    frame = inspect.currentframe()
    if verbose: print("The name of function is : ", frame.f_code.co_name)
    if pt_asss:
        msg=f"Routine :  {subroutine.name} => wrong use of some pointers : {pointers}"
    if pt_asss_derive:
        msg+=f"\n ??? wrong use of some pointers : {pointers_derive} ???"
    if len(msg)!=0:
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
rech si arrays ds expt => 1) si un seul tableau : si #mult

1) si plus de 1 tableau : pas de array syntax ds les tableaux : ok (A(:) = B(I)+C(I,J)
2) si un seul tableau :  1) if isinstance(Array) sans rien => Ok c'est une copie
                         2) else : un seul tableau mais element n'apparait pas comme tableau => ça veut dire qu'on a un opérateur => pas bon
                         
2) si aucun tableau => c'est bon
    """               

    def is_array_syntax(node):
        for var in FindVariables().visit(node):
            if isinstance(var, Array):
                for dim in var.dimensions:
                    if isinstance(dim, RangeIndex):
                        return(True)
        return(False)

    verbose=False
    msg=""
    for assign in FindNodes(Assignment).visit(subroutine.body):
        array_syntax=is_array_syntax(assign.lhs)
                            

            
        if array_syntax:
            arrays = [var for var in FindVariables().visit(assign.rhs) if isinstance(var, Array)]
            if len(arrays)>1:
                for array in arrays:
                    if is_array_syntax(array):
                        msg+=f" *** Some array syntax in {fgen(assign)}\n"
            if len(arrays)==1:
                if not isinstance(assign.rhs, Array) and is_array_syntax(arrays[0]):
                    msg+=f" *** Some array syntax in {fgen(assign)}\n"
                
##        if isinstance(assign.rhs, Array):
##            is_copy=True
##        if (isinstance(assign.rhs, FloatLiteral) or isinstance(assign.rhs, IntLiteral) or isinstance(assign.rhs, LogicLiteral)):
###        if not FindVariables().visit(assign.rhs):
##            is_init=True
###todo if rhs is a big expression of constants 
##        if (isinstance(assign.rhs, Product)):
##            if assign.rhs.children[0]==-1 and isinstance(assign.rhs.children[1], FloatLiteral):
##                is_init=True
##    
##        if (is_array_syntax and not is_copy) and (is_array_syntax and not is_init):
##            msg+=f" *** Some array syntax in {fgen(assign)}\n"
     
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
#### TODO or not ??? :::     if var is a pointer : ignore first dim check. see check5
    lst_not_nproma_pt=[var for var in lst_not_nproma if var.
    if var is a pointer : ignore first dim check.
    """
    NPROMA=["NPROMA", "KLON","YDGEOMETRY%YRDIM%NPROMA","YDCPG_OPTS%KLON","D%NIJT","KPROMA"]
    BOUNDS=["KST/KEND","KIDIA/KFDIA","YDCPG_BNDS%KIDIA/KDCPG_BNDS%KFDIA","D%NIJB/D%NIJE","D%NIB/D%NIE"]
    JLON=["JLON","JROF","JIJ","JI", "JL"]

    msg=""
    msg_nproma=""
    verbose=False
#    verbose=True

    lst_not_nproma=[]
#    arrays=[var for var in subroutine.variables if var not in subroutine.arguments and isinstance(var, Array)]
   
#1- first check that first dim of arrays in NPROMA
    arrays=[var for var in FindVariables().visit(subroutine.body) if isinstance(var, Array)]
    for var in arrays:
        if var.shape:
            if isinstance(var.shape[0], DeferredTypeSymbol)  or isinstance(var.shape[0], Scalar): 
                if var.shape[0].name not in NPROMA:
                    if verbose: msg_nproma+=f" *** var : {var.name} has none nproma dim as first dim : {var.shape[0].name}\n"
                    
                    lst_not_nproma.append(var.name)    
            else:
                lst_not_nproma.append(var.name)    
                if verbose: msg_nproma+=f" *** var : {var.name} has range index first dim !!! \n"
        elif is_derive(var):
            if is_index:
                raise NotImplementedError(f"dim is neither slice, section or scalar : dim = {dim}")
                #derived type will arrive here : TODO ::: add the index with the derived types.
            else:
                lst_not_nproma.append(var.name) 
                if verbose: msg_nproma+=f" ??? *** var : {var.name} has unknow first dim !!! ??? \n"
        else:
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
        
        loop_bounds=str(loop.bounds.lower)+'/'+str(loop.bounds.upper)

        
        loop_idx=loop.variable
       # if loop_bounds not in 
        loop_vars_=[]
        loop_vars=[]
        loop_vars_=FindVariables().visit(loop.body)
        loop_vars=[var for var in loop_vars_ if isinstance(var, Array)]       
        is_bound=loop_bounds in BOUNDS
        is_idx=loop_idx.name in JLON

#        print("loop_vars =", loop_vars)
        for var in loop_vars:
            if var.name not in lst_not_nproma:
                if bool(var.dimensions): #var may have no "dimensions", for example if var comes from a call statement.
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
   Check if MINVAL or MAXVAL are used over NPROMA dim.
   SUM can be use, but the result of the sum musn't be used in a calculation, it will break reproductibility. 
   """
   calls=[]
#   lst_sum=[]
  
   NPROMA=["NPROMA", "KLON","YDGEOMETRY%YRDIM%NPROMA","YDCPG_OPTS%KLON","D%NIJT","KPROMA"]
   msg=""
   for assign in FindNodes(Assignment).visit(subroutine.body):
       for call in FindInlineCalls().visit(assign):
#           if (call.name=="SUM"):
#               lst_sum.append(assign.lhs)
   
            if (call.name=="MINVAL") or (call.name=="MAXVAL"):
                arg=call.arguments #should be only one arg
                if len(arg)>1:
                    raise NotImplementedError("MAXVAL and MINVAL should have only one arg!")

                else:
                    args=arg[0]
                    variables_=FindVariables().visit(args)
                    variables=[var for var in variables_ if isinstance(var, Array)]
#                    print("variables = ", variables)
                    derive=False
                    wrong=False
                    for var in variables:
                        if is_derive(var):
                            if is_index:
                                 raise NotImplementedError("is_index not implemented yet")
                            else:
                                msg_derive="??? can't solve this reduction: "+fgen(assign)+" ??? \n"
                                derive=True
                        else:
                            idx=0
                            is_nproma=False
                            for shape in var.shape: #look for NPROMA dim... Won't detect wrong reduction if the horizontal idx isn't NPROMA
                                if shape in NPROMA:
                                    is_nproma=True
                                    break
                                    idx=idx+1
                            if is_nproma:
                                if isinstance(var.dimensions[idx], RangeIndex): #in a reduction ":" musn't be on the NPROMA dim.
                                    msg+="*** " + fgen(assign)+"\n"
                                    wrong=True
                                    break
                    if derive and not wrong: #if can't solve some var but there is at least one var on which the reduction is on NPROMA : not important if some var # solve.
                        msg+=msg_derive
                                    
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

if __name__ == "__main__":
    
    if debug:
        s=Sourcefile.from_file("sub.F90")
        subroutine=s["SUB"]
    else:
        file=sys.argv[1]
        s=Sourcefile.from_file(file)
        subroutine=s.subroutines[0]
        resolve_associates(subroutine)
    #    print(fgen(subroutine.body))
      

    #DFindInlineCalls().visit(assign)ummy arguments of NPROMA subroutines ::: 
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
