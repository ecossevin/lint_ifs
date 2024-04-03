from loki import *
file="sub3.F90"
name="SUB"
s=Sourcefile.from_file(file)
subroutine=s[name]
routine=subroutine

def is_derive(var):
#    if isinstance(var, DeferredTypeSymbol):
    if len(var.name_parts)>1:
       return(True)
    return(False)

def get_type(var):
    return(var.name_parts[0])
    #return([sub].variable_map[var.name[0])


variables=[var for var in FindVariables().visit(routine.body)]
assigns=[assign for assign in FindNodes(Assignment).visit(subroutine.body)]

calls=[call for call in FindInlineCalls().visit(routine.body)]
present=[call for call in calls if call.name=="PRESENT"]


def inspect_present(presents, dict_present):
    for present in presents:
        if len(present.arguments)>1:
            raise NotImplementedError("present should have only one arg, not implemented")
            
        if ass.lhs in map_logical:
            map_logical[ass.lhs.name].append(present.arguments)
        else:
            map_logical[ass.lhs.name]=[]
            map_logical[ass.lhs.name].append(present.arguments)

#1) look for VAR = smthg(PRESENT)
map_logical={}
asss=[ass for ass in FindNodes(Assignment).visit(routine.body)]

# TODO : don't just look for present but for PRESENT AND PRESENT...
for ass in asss:
    calls=[call for call in FindInlineCalls().visit(routine.body)]
    presents=[call for call in calls if call.name=="PRESENT"]
    inspect_present(presents, map_logical)
    presents=[]
#2) look for cond IF ... PRESENT or IF(map_logical)

conds=FindNodes(Conditional).visit(subroutine.body)
for cond in conds:
    pt_cond_asss=[ass for ass in FindNodes(Assignment).visit(cond) if ass.ptr] 
    calls=FindInlineCalls().visit(cond.condition)
    if calls: #IF( ... PRESENT)
        presents=[present for call in calls if call.name=="PRESENT"]
        for presents in present:
            if len(present.arguments>1):
                raise NotImplementedError("present should have only one arg, not implemented")
            lst_pt.append(present.arguments[0].name)
        #inspect_present(presents, map_if)
        
        for cond_ass in pt_cond_asss:
            if cond_ass.lhs.name in lst_pt:
                pt_asss.remove(cond_ass)
    else: #IF(LTOTO) 
        is_present=True
        if isinstance(cond.condition, Scalar):
            if cond.condition in map_logical:
                lst_pt=map_logical[cond.condition] #lst of pointers in the present clauses of the logical

                for cond_ass in pt_cond_asss:
                    if cond_ass.lhs.name in lst_pt:
                        pt_asss.remove(cond_ass)
    lst_pt=[]
    presents=[]
    calls=[]

print("resu = ", pt_asss)
