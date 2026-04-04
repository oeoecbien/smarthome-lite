"""
Schémas Pydantic pour authentification et gestion des utilisateurs.
"""
from pydantic import BaseModel, EmailStr, Field, validator
from typing import Optional, Literal
from datetime import datetime
import re


class UserCreate(BaseModel):
    """
    Schéma pour création d'un nouvel utilisateur.
    
    Validations:
        - username: 3-50 caractères alphanumériques + underscore
        - email: format email valide (optionnel)
        - password: minimum 8 caractères, au moins 1 majuscule, 1 chiffre
    """
    username: str = Field(
        ...,
        min_length=3,
        max_length=50,
        description="Nom d'utilisateur unique"
    )
    email: Optional[EmailStr] = Field(
        None,
        description="Adresse email (optionnelle)"
    )
    password: str = Field(
        ...,
        min_length=8,
        description="Mot de passe (min 8 caractères)"
    )
    
    @validator("username")
    def validate_username(cls, v):
        """Vérifie que le username ne contient que des caractères autorisés."""
        if not re.match(r"^[a-zA-Z0-9_]+$", v):
            raise ValueError("Le nom d'utilisateur ne peut contenir que des lettres, chiffres et underscores")
        return v
    
    @validator("password")
    def validate_password_strength(cls, v):
        """Vérifie la robustesse du mot de passe."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not re.search(r"[0-9]", v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "demo_user",
                "email": "demo@example.com",
                "password": "DemoUser_Pass1"
            }
        }


class UserLogin(BaseModel):
    """
    Schéma pour connexion utilisateur.
    """
    username: str = Field(..., description="Nom d'utilisateur")
    password: str = Field(..., description="Mot de passe")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username": "demo_user",
                "password": "DemoUser_Pass1"
            }
        }


class Token(BaseModel):
    """
    Schéma de réponse JWT.
    """
    access_token: str = Field(..., description="Token JWT")
    token_type: str = Field(default="bearer", description="Type de token")
    expires_in: int = Field(..., description="Durée de validité en secondes")
    
    class Config:
        json_schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "expires_in": 86400
            }
        }


class TokenData(BaseModel):
    """
    Schéma des données extraites du JWT (usage interne).
    """
    username: Optional[str] = None


class ForgotPasswordRequest(BaseModel):
    """
    Schéma pour demande de réinitialisation de mot de passe.
    """
    username_or_email: str = Field(..., description="Nom d'utilisateur ou adresse email")
    
    class Config:
        json_schema_extra = {
            "example": {
                "username_or_email": "jean"
            }
        }


class ResetPasswordRequest(BaseModel):
    """
    Schéma pour réinitialisation de mot de passe.
    """
    token: str = Field(..., description="Token de réinitialisation")
    new_password: str = Field(..., min_length=8, description="Nouveau mot de passe")
    
    @validator("new_password")
    def validate_password_strength(cls, v):
        """Vérifie la robustesse du mot de passe."""
        if not re.search(r"[A-Z]", v):
            raise ValueError("Le mot de passe doit contenir au moins une majuscule")
        if not re.search(r"[0-9]", v):
            raise ValueError("Le mot de passe doit contenir au moins un chiffre")
        return v
    
    class Config:
        json_schema_extra = {
            "example": {
                "token": "abc123def456...",
                "new_password": "NewSecurePass123"
            }
        }


class MessageResponse(BaseModel):
    """
    Schéma de réponse générique avec message.
    """
    message: str = Field(..., description="Message de réponse")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "Opération réussie"
            }
        }


class UserResponse(BaseModel):
    """
    Schéma de réponse pour informations utilisateur.
    """
    id: int
    username: str
    email: Optional[str]
    role: Literal["user", "admin"] = Field(default="user", description="Rôle de l'utilisateur")
    created_at: datetime
    
    class Config:
        from_attributes = True  # Permet conversion depuis modèle ORM
        json_schema_extra = {
            "example": {
                "id": 1,
                "username": "jean",
                "email": "jean.dupont@example.com",
                "role": "user",
                "created_at": "2025-01-15T10:30:00Z"
            }
        }
