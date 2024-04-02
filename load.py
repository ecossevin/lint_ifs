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
