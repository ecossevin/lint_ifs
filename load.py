from loki import *
file="sub3.F90"
name="SUB"
s=Sourcefile.from_file(file)
subroutine=s[name]
routine=subroutine

variables=[var for var in FindVariables().visit(routine.body)]
assigns=[assign for assign in FindNodes(Assignment).visit(subroutine.body)]
