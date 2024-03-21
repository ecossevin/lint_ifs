from loki import *
file="sub.F90"
name="SUB"
s=Sourcefile.from_file(file)
subroutine=s[name]
routine=subroutine
variables=[var for var in FindVariables().visit(routine.body)]
Assignments=FindNodes(Assignment).visit(routine.body)
loops=FindNodes(Loop).visit(routine.body)

