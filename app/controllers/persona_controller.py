from typing import List
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy import or_, extract
from sqlalchemy.orm import Session

from ..database import get_db
from ..views.persona import PersonaCreate, PersonaUpdate, PersonaRead
from ..services import persona_service

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


@router.get("/buscar/{termino}")
def buscar_personas(termino: str, db: Session = Depends(get_db)):
    termino = termino.strip()
    personas = db.query(Persona).filter(
        or_(
            Persona.first_name.ilike(f"%{termino}%"),
            Persona.last_name.ilike(f"%{termino}%"),
            Persona.email.ilike(f"%{termino}%"),
        )
    ).all()
    return personas


@router.get("/reporte/activos")
def reporte_activos(db: Session = Depends(get_db)):
    activos = db.query(Persona).filter(Persona.is_active == True).all()
    return [
        {"id": p.id, "email": p.email, "phone": p.phone, "is_active": p.is_active}
        for p in activos
    ]


@router.get("/cumpleanios/mes/{numero_mes}")
def cumpleanios_mes(numero_mes: int, db: Session = Depends(get_db)):
    if numero_mes < 1 or numero_mes > 12:
        raise HTTPException(
            status_code=400,
            detail="El mes debe ser un entero entre 1 y 12.",
        )
    personas = db.query(Persona).filter(
        extract("month", Persona.birth_date) == numero_mes
    ).all()
    return personas

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
