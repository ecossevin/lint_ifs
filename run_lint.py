
from loki import * 

#=====================================================================
#=====================================================================
#                 Dummy arguments of NPROMA subroutines
#=====================================================================
#=====================================================================

class dummy_args_alloc(GenericRule):
    """
    Checks if some dummy args are ALLOCATABLE 
    """

    @classmethod
    def check_subroutine(cls, subroutine, rule_report, config, **kwargs):
        dummy_args=[var for var in subroutine.variables if var in subroutine.arguments]
        lst_alloc=[var.name for var in dummy_args if var.type.allocatable]
        if lst_alloc:
            msg=f"Routine :  {subroutine.name} => {len(lst_alloc)} dummy args allocatable : {lst_alloc}" 
            rule_report.add(msg)

class dummy_args_pointer(GenericRule):
    """
    Checks if some dummy args are POINTER
    """

    @classmethod
    def check_subroutine(cls, subroutine, rule_report, config, **kwargs):
        dummy_args=[var for var in subroutine.variables if var in subroutine.arguments]
        lst_pointer=[var.name for var in dummy_args if var.type.pointer]
        if lst_pointer:
            msg=f"Routine :  {subroutine.name} => {len(lst_pointer)} dummy args pointer : {lst_pointer}" 
            rule_report.add(msg)

class dummy_args_intent(GenericRule):
    """
    Checks if some dummy args have no INTENT.
    """

    @classmethod
    def check_subroutine(cls, subroutine, rule_report, config, **kwargs):
        lst_no_intent=[var.name for var in subroutine.arguments if not var.type.intent]
        if lst_no_intent:
            msg=f"Routine :  {subroutine.name} => {len(lst_no_intent)} dummy args with no intent : {lst_no_intent}"
            rule_report.add(msg)
class dummy_args_assume(GenericRule):
    """
    Checks if some dummy args assumed shapes.
    """

    @classmethod
    def check_subroutine(subroutine):
        def is_assume(shapes):
            if shapes:
                for shape in shapes:
                    if type(shape)==RangeIndex:
                        return(True)
                return(False)
        lst_assume_shape=[var.name for var in subroutine.variables if (is_assume(var.type.shape))]
        if lst_assume_shape:
            msg=f"Routine :  {subroutine.name} => {len(lst_assume_shape)} dummy args with assumed shapes: {lst_assume_shape}"
            rule_report.add(msg)


class dummy_args_cst_type(GenericRule):
    """
    Checks if some particular types have wrong intent  
    Checks if YDMODEL, YDGEOMETRY have the INTENT(IN) attribute.
    """

    @classmethod
   
    def check_subroutine(subroutine):
    """
    """
    msg=""
    for variable_name in ["ydmodel", "ydgeometry"]:
    #for variable_name in ["ydmodel", "ydgeometry", "ydvars"]:
        if variable_name in subroutine.variable_map:
            variable=subroutine.variable_map[variable_name]
            if not variable.type.intent:
                msg+=f"Routine :  {subroutine.name} => {variable_name} has no intent"
                if len(msg)!=0:
                    msg=msg+"\n"
              

            else:
                if variable.type.intent!="in":
      
                    msg+=f"Routine :  {subroutine.name} => {variable_name} has wrong intent : {variable.type.intent} (not intent in)"
                    if len(msg)!=0:
                        msg=msg+"\n"

    if(len(msg)!=0):
        rule_report.add(msg)
#=====================================================================
#=====================================================================
#                 Temporaries of NPROMA subroutines
#=====================================================================
#=====================================================================


class temporaries_nproma(GenericRule):
    """
    Checks that NPROMA is the first dimension of temporaries, if not dim must be known at compile time.
    """

    @classmethod
    def check_subroutine(subroutine):
        lst_horizontal=["NPROMA", "KLON"]
        lst_not_nproma=[]
        temps=[var for var in subroutine.variables if var not in subroutine.arguments and isinstance(var, Array)]
       
        for var in temps:
            if type(var.shape[0])==DeferredTypeSymbol: 
                if var.shape[0] not in lst_horizontal:
                    lst_not_nproma.append(var.name)    
        if len(lst_not_nproma)!=0:
            msg=f"Routine :  {subroutine.name} => {len(lst_not_nproma)} temp with leading diff than nproma: {lst_not_nproma}"
            rule_report.add(msg)
class temporaries_alloc(GenericRule):
    """
    Checks if temporaries aren't ALLOCATABLE 
    """

    def check_subroutine(subroutine):
        temps=[var for var in subroutine.variables if var not in subroutine.arguments and isinstance(var, Array)]
       
        lst_alloc=[var.name for var in temps if var.type.allocatable]
        msg=""
        if lst_alloc:
            msg=f"Routine :  {subroutine.name} => {len(lst_alloc)} temp allocatable : {lst_alloc}" 
            rule_report.add(msg)
    

source = Sourcefile.from_source(fcode)
messages = []
handler = DefaultHandler(target=messages.append)
run_linter(source, [rules.dummy_args_alloc], handlers=[handler])

