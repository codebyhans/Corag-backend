from typing import List, Optional
from pydantic import BaseModel, Field

class Ingredient(BaseModel):
    identifier: str = Field(
        ..., 
        example="a-1", 
        description="A unique identifier for the ingredient, typically an alphanumeric code."
    )
    concentration: float = Field(
        ..., 
        example=0.1, 
        description="The concentration of the ingredient in the mix, expressed as a decimal fraction."
    )
    volume_constraint_lb: float = Field(
        ..., 
        example=0.0, 
        description="The lower bound on the volume of this ingredient allowed in the final mixture."
    )
    volume_constraint_ub: float = Field(
        ..., 
        example=15.0, 
        description="The upper bound on the volume of this ingredient allowed in the final mixture."
    )
    amount: Optional[float] = Field(
        None,
        example=12.5,
        description="The calculated amount of this ingredient needed to satisfy the optimization problem."
    )

class OptimizationMixingRequest(BaseModel):
    concentration_target: float = Field(
        ..., 
        example=0.7, 
        description="The target concentration for the overall mixture."
    )
    concentration_tolerance_lb: float = Field(
        ..., 
        example=0.3, 
        description="The lower bound for the tolerated excess concentration."
    )
    concentration_tolerance_ub: float = Field(
        ..., 
        example=0.2, 
        description="The upper bound for the tolerated excess cencentration."
    )
    total_volume_constraint: float = Field(
        ..., 
        example=100.0, 
        description="The total volume constraint for the mixture, representing the sum of all ingredient volumes."
    )
    ingredients: List[Ingredient] = Field(
        ..., 
        description="A list of ingredients, each with its own identifier, concentration, volume constraints, and optionally the amount needed.",
        example=[
            {
                "identifier": "a-1", 
                "concentration": 0.1, 
                "volume_constraint_lb": 0.0, 
                "volume_constraint_ub": 15.0,
            },
            {
                "identifier": "b-2", 
                "concentration": 0.2, 
                "volume_constraint_lb": 0.0, 
                "volume_constraint_ub": 56.0,
            },
            {
                "identifier": "c-3", 
                "concentration": 0.7, 
                "volume_constraint_lb": 0.0, 
                "volume_constraint_ub": 100.0,
            }
        ]
    )
