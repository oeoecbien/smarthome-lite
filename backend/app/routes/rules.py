"""
Routes pour la gestion des règles d'automatisation.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from app.database import get_db
from app.models import Rule, User
from app.schemas.rule import RuleCreate, RuleUpdate, RuleResponse
from app.dependencies import get_current_user
from app.utils.validators import validate_rule_condition, validate_rule_action

router = APIRouter()


@router.get("/", response_model=List[RuleResponse])
async def get_rules(
    enabled: bool = None,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Liste toutes les règles d'automatisation.
    """
    query = db.query(Rule)
    
    if enabled is not None:
        query = query.filter(Rule.enabled == enabled)
    
    rules = query.order_by(Rule.priority.desc(), Rule.created_at.desc()).all()
    return rules


@router.get("/{rule_id}", response_model=RuleResponse)
async def get_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Récupère une règle spécifique.
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Règle introuvable")
    
    return rule


@router.post("/", response_model=RuleResponse, status_code=status.HTTP_201_CREATED)
async def create_rule(
    rule_data: RuleCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Crée une nouvelle règle d'automatisation.
    """
    # Valider la condition
    is_valid, error = validate_rule_condition(rule_data.condition)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Condition invalide: {error}"
        )
    
    # Valider l'action
    is_valid, error = validate_rule_action(rule_data.action, db)
    if not is_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Action invalide: {error}"
        )
    
    # Créer la règle
    rule = Rule(
        name=rule_data.name,
        description=rule_data.description,
        condition=rule_data.condition,
        action=rule_data.action,
        enabled=rule_data.enabled,
        priority=rule_data.priority
    )
    
    db.add(rule)
    db.commit()
    db.refresh(rule)
    
    return rule


@router.put("/{rule_id}", response_model=RuleResponse)
async def update_rule(
    rule_id: int,
    rule_data: RuleUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Met à jour une règle existante.
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Règle introuvable")
    
    # Mise à jour des champs
    if rule_data.name is not None:
        rule.name = rule_data.name
    if rule_data.description is not None:
        rule.description = rule_data.description
    if rule_data.condition is not None:
        # Valider la nouvelle condition
        is_valid, error = validate_rule_condition(rule_data.condition)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Condition invalide: {error}"
            )
        rule.condition = rule_data.condition
    if rule_data.action is not None:
        # Valider la nouvelle action
        is_valid, error = validate_rule_action(rule_data.action, db)
        if not is_valid:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail=f"Action invalide: {error}"
            )
        rule.action = rule_data.action
    if rule_data.enabled is not None:
        rule.enabled = rule_data.enabled
    if rule_data.priority is not None:
        rule.priority = rule_data.priority
    
    db.commit()
    db.refresh(rule)
    
    return rule


@router.delete("/{rule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_rule(
    rule_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Supprime une règle.
    """
    rule = db.query(Rule).filter(Rule.id == rule_id).first()
    if not rule:
        raise HTTPException(status_code=404, detail="Règle introuvable")
    
    db.delete(rule)
    db.commit()
    
    return None

