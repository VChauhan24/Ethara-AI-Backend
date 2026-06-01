from typing import List, Optional
from pydantic import BaseModel, EmailStr, conint, PositiveInt, constr


class ProductBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    sku: constr(strip_whitespace=True, min_length=1)
    description: Optional[str] = None
    price: float
    stock: conint(ge=0)


class ProductCreate(ProductBase):
    pass


class ProductOut(ProductBase):
    id: int

    class Config:
        from_attributes = True


class CustomerBase(BaseModel):
    name: constr(strip_whitespace=True, min_length=1)
    email: EmailStr
    phone: Optional[str] = None


class CustomerCreate(CustomerBase):
    pass


class CustomerOut(CustomerBase):
    id: int

    class Config:
        from_attributes = True


class OrderItemCreate(BaseModel):
    product_id: int
    quantity: PositiveInt


class OrderCreate(BaseModel):
    customer_id: int
    items: List[OrderItemCreate]


class OrderItemOut(BaseModel):
    product_id: int
    quantity: int
    unit_price: float

    class Config:
        from_attributes = True


class OrderOut(BaseModel):
    id: int
    customer_id: int
    total_amount: float
    items: List[OrderItemOut]

    class Config:
        from_attributes = True
