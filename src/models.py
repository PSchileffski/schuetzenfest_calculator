from enum import Enum
from typing import List, Dict, Optional, Union
from pydantic import BaseModel, Field

class CostType(str, Enum):
    FIXED = "fixed"
    PER_VISITOR = "per_visitor"
    PER_HOUR = "per_hour"
    # Can be extended, e.g., PER_HECTOLITER

class RevenueType(str, Enum):
    FIXED = "fixed"
    PER_VISITOR = "per_visitor"
    PER_UNIT_SOLD = "per_unit_sold"

class RevenueItem(BaseModel):
    name: str
    amount: float
    revenue_type: RevenueType = RevenueType.FIXED
    description: Optional[str] = None
    consumption_per_visitor: Optional[float] = Field(None, description="Average units consumed per visitor")

class CostItem(BaseModel):
    name: str
    amount: float
    cost_type: CostType = CostType.FIXED
    description: Optional[str] = None
    # For PER_HOUR or other types, we might need a multiplier defined in the scenario context
    multiplier_key: Optional[str] = Field(None, description="Key to look up in scenario stats (e.g., 'duration_hours')")

class ModuleVariant(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    cost_items: List[CostItem] = []
    revenue_items: List[RevenueItem] = []

class ModuleScope(str, Enum):
    GLOBAL = "global"
    DAILY = "daily"
    BOTH = "both"

class Module(BaseModel):
    id: str
    name: str
    scope: ModuleScope = ModuleScope.BOTH
    variants: List[ModuleVariant]

class Product(BaseModel):
    id: str
    name: str
    sales_price: float
    purchase_price: float  # or cost_per_unit
    unit: str = "Stk"

class Persona(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    # Map product_id to amount consumed per day
    consumption: Dict[str, float] = {}
    # Map module_id to adoption rate (0.0 to 1.0). Default is 1.0
    module_adoption_rates: Dict[str, float] = {}

class DayConfig(BaseModel):
    name: str  # e.g., "Friday"
    enabled: bool = True
    # Map persona_id to count
    visitor_composition: Dict[str, int] = {}
    duration_hours: int
    # New: Modules specific to this day
    selected_modules: Dict[str, str] = {}
    # Optional: Specific revenue items for this day (e.g. special ticket)
    day_specific_revenue: List['RevenueItem'] = []

    @property
    def total_visitors(self) -> int:
        return sum(self.visitor_composition.values())

class Scenario(BaseModel):
    id: str
    name: str
    description: Optional[str] = None
    days: List[DayConfig]
    # Map module_id to variant_id (Global Modules)
    global_modules: Dict[str, str] = {}
    # Deprecated: for backward compatibility
    selected_variants: Dict[str, str] = {}
    # Global overrides or specific parameters
    global_parameters: Dict[str, float] = {}
    # We can define products/personas here or load them globally. 
    # For simplicity in this file-based approach, let's assume they are loaded separately 
    # but we might want scenario-specific overrides? 
    # Let's keep it simple: The calculator will need access to the master data.
    revenue_items: List[RevenueItem] = [] # Global revenue items (e.g. Sponsoring)
