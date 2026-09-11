from datetime import datetime
from math import ceil
import csv, io
from fastapi import APIRouter, Depends, Query, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from app.database.session import get_db
from app.schemas.pallet import PalletPage, PalletizeRequest, PalletizeResult
from app.services.pallet_service import PalletService
from app.core.security import get_current_user, require_roles
from app.models.user import User
from app.services.audit_service import write_audit

router=APIRouter(prefix='/pallets',tags=['Pallets']); service=PalletService()
def filters(status=None,line_id=None,product_id=None,pallet_code=None,production_order=None,date_from=None,date_to=None):return dict(status=status,line_id=line_id,product_id=product_id,pallet_code=pallet_code,production_order=production_order,date_from=date_from,date_to=date_to)

@router.get('',response_model=PalletPage)
def list_pallets(page:int=Query(1,ge=1),page_size:int=Query(20,ge=8,le=100),status:str|None=None,line_id:int|None=Query(None,gt=0),product_id:int|None=Query(None,gt=0),pallet_code:str|None=None,production_order:str|None=None,date_from:datetime|None=None,date_to:datetime|None=None,db:Session=Depends(get_db), _:User=Depends(require_roles("SUPERVISOR","ADMIN"))):
    items,total=service.list_page(db,page=page,page_size=page_size,**filters(status,line_id,product_id,pallet_code,production_order,date_from,date_to)); return {'items':items,'total':total,'page':page,'page_size':page_size,'total_pages':max(1,ceil(total/page_size))}

@router.get('/export.csv')
def export_pallets(status:str|None=None,line_id:int|None=Query(None,gt=0),product_id:int|None=Query(None,gt=0),pallet_code:str|None=None,production_order:str|None=None,date_from:datetime|None=None,date_to:datetime|None=None,db:Session=Depends(get_db), _:User=Depends(require_roles("SUPERVISOR","ADMIN"))):
    items=service.repository.list_pallets_export(db,**filters(status,line_id,product_id,pallet_code,production_order,date_from,date_to)); out=io.StringIO(); w=csv.writer(out,delimiter=';'); w.writerow(['ID','Código','Produto ID','Linha ID','Quantidade','Capacidade','Status','Abertura','Conclusão'])
    for x in items:w.writerow([x.id,x.pallet_code,x.product_id,x.line_id,x.current_quantity,x.target_quantity,x.status,x.opened_at.isoformat(sep=' '),x.completed_at.isoformat(sep=' ') if x.completed_at else ''])
    return StreamingResponse(iter([('\ufeff'+out.getvalue()).encode('utf-8')]),media_type='text/csv; charset=utf-8',headers={'Content-Disposition':'attachment; filename="autopackline_paletes.csv"'})

@router.get('/{pallet_id}')
def get_pallet_detail(pallet_id:int,db:Session=Depends(get_db), _:User=Depends(require_roles("SUPERVISOR","ADMIN"))):
    d=service.repository.get_pallet_detail(db,pallet_id)
    if not d: raise HTTPException(404,'Palete não encontrado')
    p,o,l,product,rows=d
    return {'id':p.id,'pallet_code':p.pallet_code,'line_id':p.line_id,'product_id':p.product_id,'production_order_id':p.production_order_id,'target_quantity':p.target_quantity,'current_quantity':p.current_quantity,'status':p.status,'opened_at':p.opened_at,'completed_at':p.completed_at,'closed_at':p.closed_at,'production_order':o.order_number if o else None,'lot_code':o.lot_code if o else None,'product_model':product.model if product else None,'product_ean':product.ean if product else None,'line_code':l.code if l else None,'items':[{'sequence_number':i.sequence_number,'position':i.position,'added_at':i.added_at,'production_unit_id':u.id,'serial_number':u.serial_number} for i,u in rows]}

@router.post('/palletize',response_model=PalletizeResult)
def palletize(payload:PalletizeRequest,db:Session=Depends(get_db), actor:User=Depends(get_current_user)):
    result=service.palletize(db,payload)
    write_audit(db, "PALLETIZE_CONFIRMED", actor, "PALLET", result.pallet.id, {"production_unit_id": result.production_unit_id, "sequence": result.sequence_number, "completed_now": result.completed_now})
    return result
