from datetime import datetime
from math import ceil
import csv, io
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.scan import ScanPage, ScanRead, ScanSimulateRequest, ScanSimulationResult, TestQrResponse
from app.services.scan_service import ScanService
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.services.audit_service import write_audit

router = APIRouter(prefix="/scans", tags=["Scans"])
service = ScanService()

def filters(status=None,line_id=None,serial=None,ean=None,production_order=None,date_from=None,date_to=None):
    return dict(status=status,line_id=line_id,serial=serial,ean=ean,production_order=production_order,date_from=date_from,date_to=date_to)

@router.get("", response_model=ScanPage)
def list_scans(page:int=Query(1,ge=1),page_size:int=Query(20,ge=8,le=100),status:str|None=None,line_id:int|None=Query(None,gt=0),serial:str|None=None,ean:str|None=None,production_order:str|None=None,date_from:datetime|None=None,date_to:datetime|None=None,db:Session=Depends(get_db), _:User=Depends(require_roles("SUPERVISOR","ADMIN"))):
    items,total=service.list_page(db,page=page,page_size=page_size,**filters(status,line_id,serial,ean,production_order,date_from,date_to))
    return {"items":items,"total":total,"page":page,"page_size":page_size,"total_pages":max(1,ceil(total/page_size))}

@router.get("/export.csv")
def export_scans(status:str|None=None,line_id:int|None=Query(None,gt=0),serial:str|None=None,ean:str|None=None,production_order:str|None=None,date_from:datetime|None=None,date_to:datetime|None=None,db:Session=Depends(get_db), _:User=Depends(require_roles("SUPERVISOR","ADMIN"))):
    items=service.repository.list_scans_export(db,**filters(status,line_id,serial,ean,production_order,date_from,date_to))
    out=io.StringIO(); w=csv.writer(out,delimiter=';'); w.writerow(['ID','Status','Serial','EAN','OP','Linha','Data/Hora','Erro'])
    for x in items:w.writerow([x.id,x.status,x.serial_number or '',x.ean or '',x.production_order or '',x.line_id,x.scanned_at.isoformat(sep=' '),x.error_message or ''])
    data=('\ufeff'+out.getvalue()).encode('utf-8')
    return StreamingResponse(iter([data]),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="autopackline_leituras.csv"'})

@router.get("/test-code", response_model=TestQrResponse)
def generate_test_qr(production_order_id:int=Query(...,gt=0),db:Session=Depends(get_db), _:User=Depends(get_current_user)):
    return service.generate_test_qr(db, production_order_id)

@router.get("/{scan_id}", response_model=ScanRead)
def get_scan(scan_id:int,db:Session=Depends(get_db), _:User=Depends(require_roles("SUPERVISOR","ADMIN"))):
    item=service.repository.get_scan(db,scan_id)
    if not item: raise HTTPException(404,'Leitura não encontrada')
    return item

@router.post("/simulate", response_model=ScanSimulationResult)
def simulate_scan(payload:ScanSimulateRequest,db:Session=Depends(get_db), actor:User=Depends(get_current_user)):
    result = service.simulate(db,payload)
    write_audit(db, "SCAN_EXECUTED", actor, "SCAN_EVENT", result.scan.id, {"status": result.scan.status, "line_id": payload.line_id, "serial": result.scan.serial_number})
    return result
