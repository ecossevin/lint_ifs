from loki import *
file="sub.F90"
name="SUB"
s=Sourcefile.from_file(file)
subroutine=s[name]
routine=subroutine
calls=FindNodes(CallStatement).visit(subroutine.body)

