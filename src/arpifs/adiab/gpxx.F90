SUBROUTINE GPXX(YDGEOMETRY, KFLEV, KPROMA, KST, KEND, PHIHL, PHIHM, PHIFL, PHIFM, &
& PLNPR, PRT, PUF, PVF, PUH, PVH, PX, PNHPPI, LDVFE  )

! GPXX - Diagnose NHX-term

! Purpose
! -------
!   Diagnose NHX-term 
!    NHX = (pre/(RT)) grad[gz] (d V / d prehyd)
!   It is better to rewrite NHX as follows for the discretisation:
!    NHX = (pre/prehyd) (1/(RT)) grad[gz] ( d V / d (log(prehyd)) )

!   NHX is discretised as follows, at full levels, for FD discretisation:
!   [X]_[l] = [pre/prehyd]_[l] * [ 1/(R_[l] T_[l] delta_[l]) ] *
!             [ grad[gz]_[lbar-1] (V_[l] - V[lbar-1])
!             + grad[gz]_[lbar] (V_[lbar] - V_[l]) ]
!   VFE discretisation is different.

!   This routine can be used in a NHEE model: PNHPPI should be present in this case.

!   This routine can also be used in a hydrostatic model or in a NHQE model:
!   in this case the ratio (pre/prehyd) is equal to 1 and PNHPPI should not be used.

! Interface
! ---------
!   * INPUT:
!   YDGEOMETRY   : structure containing all geometry
!   KFLEV        : number of levels.
!   KPROMA       : length of work
!   KSTART       : start of work
!   KEND         : end of work
!   PHIHL        : zonal component of "grad[gz]" at half levels.
!   PHIHM        : meridian component of "grad[gz]" at half levels.
!   PHIFL        : zonal component of "grad[gz]" at full levels.
!   PHIFM        : meridian component of "grad[gz]" at full levels.
!   PLNPR        : "delta" at full levels.
!   PRT          : (R*Temperature) at full levels.
!   PUF          : U-wind at full levels.
!   PVF          : V-wind at full levels.
!   PUH          : U-wind at half levels.
!   PVH          : V-wind at half levels.

!   * OUTPUT:
!   PX           : NHX-term at full levels.

!   * OPTIONAL INPUT:
!   PNHPPI       : [pre/prehyd] at full levels (NHEE model).
!   LDVFE        : T if VFE discretisation is used in this routine.

! Externals
! ---------

! Method
! ------

! Reference
! ---------

! Author
! ------
!   06 Dec 2004 K. Yessad (after GNHX).

! Modifications
! -------------
!   N. Wedi and K. Yessad (Jan 2008): different dev for NH model and PC scheme
!   K. Yessad (March 2009): correct false comments for LRWSDLG=T
!   J. Vivoda (Oct 2013): new options for VFE-NH
!   K. Yessad (June 2017): Introduce NHQE model.
!   J. Vivoda and P. Smolikova (Sep 2017): new options for VFE-NH
!   K. Yessad (Feb 2018): remove deep-layer formulations.
!   J. Vivoda and P. Smolikova (Sep 2020): VFE pruning.
!   R. El Khatib 31-Jan-2022 Optional VFE
!   C. Wastl and C. Wittmann (Feb 2022): Add updraft helicity 
! End Modifications
!---------------------------------------------------------------------

USE PARKIND1     , ONLY : JPIM, JPRB, JPRD
USE YOMHOOK      , ONLY : LHOOK, DR_HOOK, JPHOOK
USE GEOMETRY_MOD , ONLY : GEOMETRY



! -----------------------------------------------------------------------------

IMPLICIT NONE

TYPE(GEOMETRY)     ,INTENT(IN)             :: YDGEOMETRY
INTEGER(KIND=JPIM) ,INTENT(IN)             :: KFLEV
INTEGER(KIND=JPIM) ,INTENT(IN)             :: KPROMA 
INTEGER(KIND=JPIM) ,INTENT(IN)             :: KST 
INTEGER(KIND=JPIM) ,INTENT(IN)             :: KEND 
REAL(KIND=JPRB)    ,INTENT(IN)             :: PHIHL(KPROMA,0:KFLEV) 
REAL(KIND=JPRB)    ,INTENT(IN)             :: PHIHM(KPROMA,0:KFLEV) 
REAL(KIND=JPRB)    ,INTENT(IN)             :: PHIFL(KPROMA,KFLEV) 
REAL(KIND=JPRB)    ,INTENT(IN)             :: PHIFM(KPROMA,KFLEV) 
REAL(KIND=JPRB)    ,INTENT(IN)             :: PLNPR(KPROMA,KFLEV) 
REAL(KIND=JPRB)    ,INTENT(IN)             :: PRT(KPROMA,KFLEV) 
REAL(KIND=JPRB)    ,INTENT(IN)             :: PUF(KPROMA,KFLEV) 
REAL(KIND=JPRB)    ,INTENT(IN)             :: PVF(KPROMA,KFLEV) 
REAL(KIND=JPRB)    ,INTENT(IN)             :: PUH(KPROMA,0:KFLEV) 
REAL(KIND=JPRB)    ,INTENT(IN)             :: PVH(KPROMA,0:KFLEV) 
REAL(KIND=JPRB)    ,INTENT(OUT)            :: PX(KPROMA,KFLEV) 
REAL(KIND=JPRB)    ,INTENT(IN)  ,OPTIONAL  :: PNHPPI(KPROMA,KFLEV) 
LOGICAL, OPTIONAL, INTENT(IN)    :: LDVFE

! -----------------------------------------------------------------------------

INTEGER(KIND=JPIM) :: JLEV, JROF
REAL(KIND=JPRB) :: ZDUF(KPROMA,KFLEV)
REAL(KIND=JPRB) :: ZDVF(KPROMA,KFLEV)
REAL(KIND=JPRB) :: ZF(KPROMA,0:KFLEV+1)
LOGICAL :: LLVFE

REAL(KIND=JPHOOK) :: ZHOOK_HANDLE

! -----------------------------------------------------------------------------

#include "verdisint.intfb.h"

! -----------------------------------------------------------------------------

IF (LHOOK) CALL DR_HOOK('GPXX', 0, ZHOOK_HANDLE)

! -----------------------------------------------------------------------------

IF (PRESENT(LDVFE)) THEN
  LLVFE = LDVFE
ELSE
  LLVFE = YDGEOMETRY%YRVERT_GEOM%YRCVER%LVERTFE
ENDIF

IF (LLVFE) THEN

  ! vertical derivatives of wind
  ZF(KST:KEND,0)       = 0.0_JPRB
  ZF(KST:KEND,KFLEV+1) = 0.0_JPRB
  ZF(KST:KEND,1:KFLEV) = PUF(KST:KEND,1:KFLEV)
  CALL VERDISINT(YDGEOMETRY%YRVERT_GEOM%YRVFE,YDGEOMETRY%YRVERT_GEOM%YRCVER,'FDER','11',KPROMA,KST,KEND,KFLEV,ZF,ZDUF)
  ZF(KST:KEND,1:KFLEV) = PVF(KST:KEND,1:KFLEV)
  CALL VERDISINT(YDGEOMETRY%YRVERT_GEOM%YRVFE,YDGEOMETRY%YRVERT_GEOM%YRCVER,'FDER','11',KPROMA,KST,KEND,KFLEV,ZF,ZDVF)

  IF (PRESENT(PNHPPI)) THEN
    DO JLEV=1,KFLEV
      DO JROF=KST,KEND
        PX(JROF,JLEV) =&
         & REAL(PNHPPI(JROF,JLEV),JPRD)/REAL(PRT(JROF,JLEV)*PLNPR(JROF,JLEV),JPRD)*&
         & REAL(PHIFL(JROF,JLEV)*ZDUF(JROF,JLEV)+PHIFM(JROF,JLEV)*ZDVF(JROF,JLEV),JPRD)&
         & /YDGEOMETRY%YRVERT_GEOM%YRVETA%VFE_RDETAH(JLEV)
      ENDDO
    ENDDO
  ELSE
    DO JLEV=1,KFLEV
      DO JROF=KST,KEND
        PX(JROF,JLEV) =&
         & 1._JPRD/REAL(PRT(JROF,JLEV)*PLNPR(JROF,JLEV),JPRD)*&
         & REAL(PHIFL(JROF,JLEV)*ZDUF(JROF,JLEV)+PHIFM(JROF,JLEV)*ZDVF(JROF,JLEV),JPRD)&
         & /YDGEOMETRY%YRVERT_GEOM%YRVETA%VFE_RDETAH(JLEV)
      ENDDO
    ENDDO
  ENDIF

ELSE

  IF (PRESENT(PNHPPI)) THEN
    DO JLEV=1,KFLEV
      DO JROF=KST,KEND
        PX(JROF,JLEV)=( &
         & REAL(PUH(JROF,JLEV)-PUF(JROF,JLEV),JPRD)*PHIHL(JROF,JLEV) + &
         & REAL(PVH(JROF,JLEV)-PVF(JROF,JLEV),JPRD)*PHIHM(JROF,JLEV) + &
         & REAL(PUF(JROF,JLEV)-PUH(JROF,JLEV-1),JPRD)*PHIHL(JROF,JLEV-1) + &
         & REAL(PVF(JROF,JLEV)-PVH(JROF,JLEV-1),JPRD)*PHIHM(JROF,JLEV-1) &
         & )*REAL(PNHPPI(JROF,JLEV),JPRD)/REAL(PRT(JROF,JLEV)*PLNPR(JROF,JLEV),JPRD)
      ENDDO
    ENDDO
  ELSE
    DO JLEV=1,KFLEV
      DO JROF=KST,KEND
        PX(JROF,JLEV)=( &
         & REAL(PUH(JROF,JLEV)-PUF(JROF,JLEV),JPRD)*PHIHL(JROF,JLEV) + &
         & REAL(PVH(JROF,JLEV)-PVF(JROF,JLEV),JPRD)*PHIHM(JROF,JLEV) + &
         & REAL(PUF(JROF,JLEV)-PUH(JROF,JLEV-1),JPRD)*PHIHL(JROF,JLEV-1) + &
         & REAL(PVF(JROF,JLEV)-PVH(JROF,JLEV-1),JPRD)*PHIHM(JROF,JLEV-1) &
         & )/REAL(PRT(JROF,JLEV)*PLNPR(JROF,JLEV),JPRD)
      ENDDO
    ENDDO
  ENDIF

ENDIF

! -----------------------------------------------------------------------------

IF (LHOOK) CALL DR_HOOK('GPXX', 1, ZHOOK_HANDLE)

END SUBROUTINE GPXX

