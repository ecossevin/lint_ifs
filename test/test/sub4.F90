SUBROUTINE SUB4(A, YDMODEL, YDGEOMETRY)

USE TYPE_MODEL         , ONLY : MODEL
IMPLICIT NONE 

TYPE(MODEL), INTENT(INOUT) :: YDMODEL
TYPE(MODEL), INTENT(OUT) :: YDGEOMETRY

REAL (KIND=JPRB) :: A(:, :)

END SUBROUTINE
