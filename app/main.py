import os
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from . import models, schemas
from .database import SessionLocal, engine


app = FastAPI(title='Product Customer Order API')

app.add_middleware(
    CORSMiddleware,
    allow_origins=[],  # use regex instead to echo Origin header
    allow_origin_regex=r".*",
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)

import logging
logging.getLogger().info('CORS middleware configured: allow_origin_regex=.* allow_credentials=True')


@app.on_event("startup")
def create_tables_on_startup():
    try:
        if engine is not None:
            models.Base.metadata.create_all(bind=engine)
        else:
            import logging
            logging.warning('Database engine not available at startup; skipping create_all.')
    except Exception as exc:
        import logging
        logging.exception("Failed creating tables on startup: %s", exc)


def get_db():
    if SessionLocal is None:
        raise HTTPException(status_code=503, detail='Database unavailable')
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@app.post('/products', response_model=schemas.ProductOut, status_code=201)
def create_product(product: schemas.ProductCreate, db: Session = Depends(get_db)):
    db_product = models.Product(**product.dict())
    db.add(db_product)
    try:
        db.commit()
        db.refresh(db_product)
    except IntegrityError as exc:
        db.rollback()
        if 'unique constraint' in str(exc).lower() or 'duplicate key value' in str(exc).lower():
            raise HTTPException(status_code=400, detail='Product SKU must be unique.')
        raise
    return db_product


@app.get('/products', response_model=list[schemas.ProductOut])
def list_products(db: Session = Depends(get_db)):
    return db.query(models.Product).order_by(models.Product.id).all()


@app.post('/customers', response_model=schemas.CustomerOut, status_code=201)
def create_customer(customer: schemas.CustomerCreate, db: Session = Depends(get_db)):
    db_customer = models.Customer(**customer.dict())
    db.add(db_customer)
    try:
        db.commit()
        db.refresh(db_customer)
    except IntegrityError as exc:
        db.rollback()
        if 'unique constraint' in str(exc).lower() or 'duplicate key value' in str(exc).lower():
            raise HTTPException(status_code=400, detail='Customer email must be unique.')
        raise
    return db_customer


@app.get('/customers', response_model=list[schemas.CustomerOut])
def list_customers(db: Session = Depends(get_db)):
    return db.query(models.Customer).order_by(models.Customer.id).all()


@app.post('/orders', response_model=schemas.OrderOut, status_code=201)
def create_order(order_in: schemas.OrderCreate, db: Session = Depends(get_db)):
    customer = db.query(models.Customer).filter(models.Customer.id == order_in.customer_id).first()
    if not customer:
        raise HTTPException(status_code=400, detail='Customer not found.')

    items = []
    total_amount = 0.0

    for item_in in order_in.items:
        product = db.query(models.Product).filter(models.Product.id == item_in.product_id).with_for_update().first()
        if not product:
            raise HTTPException(status_code=400, detail=f'Product ID {item_in.product_id} not found.')
        if product.stock < item_in.quantity:
            raise HTTPException(
                status_code=400,
                detail=f'Insufficient stock for product {product.name} (SKU: {product.sku}).',
            )
        product.stock -= item_in.quantity
        line_total = float(product.price) * item_in.quantity
        total_amount += line_total
        items.append(models.OrderItem(product_id=product.id, quantity=item_in.quantity, unit_price=product.price))

    order = models.Order(customer_id=customer.id, total_amount=total_amount, items=items)
    db.add(order)
    db.commit()
    db.refresh(order)

    return schemas.OrderOut(
        id=order.id,
        customer_id=order.customer_id,
        total_amount=float(order.total_amount),
        items=[
            schemas.OrderItemOut(
                product_id=item.product_id,
                quantity=item.quantity,
                unit_price=float(item.unit_price),
            )
            for item in order.items
        ],
    )


@app.get('/orders', response_model=list[schemas.OrderOut])
def list_orders(db: Session = Depends(get_db)):
    orders = db.query(models.Order).order_by(models.Order.id).all()
    return [
        schemas.OrderOut(
            id=order.id,
            customer_id=order.customer_id,
            total_amount=float(order.total_amount),
            items=[
                schemas.OrderItemOut(
                    product_id=item.product_id,
                    quantity=item.quantity,
                    unit_price=float(item.unit_price),
                )
                for item in order.items
            ],
        )
        for order in orders
    ]
