from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session
from app.core.security import get_current_user, require_roles
from app.database.session import get_db
from app.models.user import User
from app.schemas.work_schedule import (
    DowntimeClose, DowntimeCreate, DowntimePage, DowntimeRead, PlannedBreakCreate, PlannedBreakPage,
    PlannedBreakRead, PlannedBreakUpdate, WorkScheduleSummary, WorkShiftCreate, WorkShiftPage, WorkShiftRead, WorkShiftUpdate,
)
from app.services.work_schedule_service import WorkScheduleService

router = APIRouter(prefix="/work-schedules", tags=["Work schedules"])
service = WorkScheduleService()

@router.get("/summary", response_model=WorkScheduleSummary)
def summary(db: Session = Depends(get_db), _: User = Depends(get_current_user)):
    return service.summary(db)

@router.get("/shifts", response_model=WorkShiftPage)
def list_shifts(page: int=Query(1,ge=1), page_size: int=Query(5,ge=1,le=50), line_id: int|None=Query(None,gt=0), active: bool|None=None, db: Session=Depends(get_db), _: User=Depends(get_current_user)):
    return service.list_shifts(db,page=page,page_size=page_size,line_id=line_id,active=active)

@router.post("/shifts", response_model=WorkShiftRead, status_code=status.HTTP_201_CREATED)
def create_shift(payload: WorkShiftCreate, db: Session=Depends(get_db), actor: User=Depends(require_roles("ADMIN"))):
    return service.create_shift(db,payload,actor)

@router.put("/shifts/{shift_id}", response_model=WorkShiftRead)
def update_shift(shift_id:int,payload:WorkShiftUpdate,db:Session=Depends(get_db),actor:User=Depends(require_roles("ADMIN"))):
    return service.update_shift(db,shift_id,payload,actor)

@router.get("/breaks", response_model=PlannedBreakPage)
def list_breaks(page:int=Query(1,ge=1),page_size:int=Query(5,ge=1,le=50),shift_id:int|None=Query(None,gt=0),active:bool|None=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return service.list_breaks(db,page=page,page_size=page_size,shift_id=shift_id,active=active)

@router.post("/breaks", response_model=PlannedBreakRead, status_code=status.HTTP_201_CREATED)
def create_break(payload:PlannedBreakCreate,db:Session=Depends(get_db),actor:User=Depends(require_roles("ADMIN"))):
    return service.create_break(db,payload,actor)

@router.put("/breaks/{break_id}", response_model=PlannedBreakRead)
def update_break(break_id:int,payload:PlannedBreakUpdate,db:Session=Depends(get_db),actor:User=Depends(require_roles("ADMIN"))):
    return service.update_break(db,break_id,payload,actor)

@router.get("/downtimes", response_model=DowntimePage)
def list_downtimes(page:int=Query(1,ge=1),page_size:int=Query(6,ge=1,le=50),line_id:int|None=Query(None,gt=0),status_filter:str|None=Query(None,alias="status"),category:str|None=None,db:Session=Depends(get_db),_:User=Depends(get_current_user)):
    return service.list_downtimes(db,page=page,page_size=page_size,line_id=line_id,status=status_filter,category=category)

@router.post("/downtimes", response_model=DowntimeRead, status_code=status.HTTP_201_CREATED)
def create_downtime(payload:DowntimeCreate,db:Session=Depends(get_db),actor:User=Depends(require_roles("SUPERVISOR","ADMIN"))):
    return service.create_downtime(db,payload,actor)

@router.post("/downtimes/{event_id}/close", response_model=DowntimeRead)
def close_downtime(event_id:int,payload:DowntimeClose,db:Session=Depends(get_db),actor:User=Depends(require_roles("SUPERVISOR","ADMIN"))):
    return service.close_downtime(db,event_id,payload.ended_at,actor)
