import csv
import io
from typing import List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from ..database import get_db
from ..views.persona import PersonaCreate, PersonaUpdate, PersonaRead, EstadisticasEdadRead, BulkDesactivarRequest, BulkDesactivarResponse
from ..services import persona_service
from ..models.persona import Persona

router = APIRouter(prefix="/personas", tags=["personas"])


@router.post("", response_model=PersonaRead, status_code=status.HTTP_201_CREATED)
def create_persona(persona_in: PersonaCreate, db: Session = Depends(get_db)):
    """Create a new Persona delegating to service layer."""
    # Let domain errors bubble up to global handlers
    return persona_service.create_persona(db, persona_in)


@router.get("", response_model=List[PersonaRead])
def list_personas(
    skip: int = Query(0, ge=0),
    limit: int = Query(100, ge=1, le=1000),
    db: Session = Depends(get_db),
):
    """List Personas with pagination via service layer."""
    return persona_service.list_personas(db, skip=skip, limit=limit)


@router.get("/estadisticas/edad", response_model=EstadisticasEdadRead)
def estadisticas_edad(db: Session = Depends(get_db)):
    """D. Edad promedio (1 decimal), mínima y máxima según birth_date."""
    return persona_service.estadisticas_edad(db)


@router.patch("/bulk/desactivar", response_model=BulkDesactivarResponse)
def desactivar_masivo(body: BulkDesactivarRequest, db: Session = Depends(get_db)):
    """H. Desactiva una lista de IDs (1 a 100) y reporta los no encontrados."""
    if len(body.ids) == 0:
        raise HTTPException(status_code=400, detail="La lista de ids no puede estar vacía.")
    if len(body.ids) > 100:
        raise HTTPException(status_code=400, detail="La lista de ids no puede tener más de 100 elementos.")
    return persona_service.desactivar_masivo(db, body.ids)


@router.get("/exportar/csv")
def exportar_csv(db: Session = Depends(get_db)):
    """I. Exporta todos los registros en formato CSV (descarga personas.csv)."""
    personas = persona_service.listar_todas(db)  # se leen antes de empezar a "streamear"

    def generar_csv():
        buffer = io.StringIO()
        writer = csv.writer(buffer)

        def flush() -> str:
            data = buffer.getvalue()
            buffer.seek(0)
            buffer.truncate(0)
            return data

        writer.writerow(
            ["id", "first_name", "last_name", "email", "phone", "birth_date", "is_active", "notes"]
        )
        yield flush()
        for p in personas:
            writer.writerow([
                p.id,
                p.first_name,
                p.last_name,
                p.email,
                p.phone or "",
                p.birth_date.isoformat() if p.birth_date else "",
                "true" if p.is_active else "false",
                p.notes or "",
            ])
            yield flush()

    return StreamingResponse(
        generar_csv(),
        media_type="text/csv",
        headers={"Content-Disposition": 'attachment; filename="personas.csv"'},
    )


@router.get("/{persona_id}", response_model=PersonaRead)
def get_persona(persona_id: int, db: Session = Depends(get_db)):
    """Retrieve a Persona by ID via service layer."""
    return persona_service.get_persona(db, persona_id)


@router.put("/{persona_id}", response_model=PersonaRead)
def update_persona(persona_id: int, persona_in: PersonaUpdate, db: Session = Depends(get_db)):
    """Update an existing Persona (partial) via service layer."""
    return persona_service.update_persona(db, persona_id, persona_in)


@router.delete("/{persona_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_persona(persona_id: int, db: Session = Depends(get_db)):
    """Delete a Persona by ID via service layer."""
    persona_service.delete_persona(db, persona_id)
    return None
