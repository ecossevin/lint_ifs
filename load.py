from loki import *
file="sub2.F90"
name="SUB"
s=Sourcefile.from_file(file)
subroutine=s[name]
routine=subroutine

calls=[]
for assign in FindNodes(Assignment).visit(routine.body):
    for call in FindInlineCalls().visit(assign):
        calls.append(call)
