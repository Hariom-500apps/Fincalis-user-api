"""API CRUD"""

from typing import Optional
from fastapi import Depends
from pydantic import ValidationError
from sqlmodel import SQLModel, Session,select as _select

from .db import get_db
from .util import response
from sqlalchemy.engine.row import Row
from sqlalchemy import and_
from sqlalchemy.orm import load_only
from datetime import datetime



def serialize_row(row: Row) -> dict:
    """Serialize SQLAlchemy Row object to a dictionary"""
    return {column: value for column, value in row._mapping.items()}


def load_only_columns(
        query: _select,
        entity: SQLModel,
        columns: Optional[list] = None,
    ):
        """Load only will show selected columns"""
        load_only_columns = [getattr(entity, field) for field in columns]

        query = query.with_entities(*load_only_columns)
        return query


async def get_all(db_model, db, message, columns=None, filters=None):
    try:
        query = db.query(db_model)
        
        if filters:
            filter_conditions = [getattr(db_model, key) == value for key, value in filters.items()]
            query = query.filter(and_(*filter_conditions))
        
        if columns:
            query = load_only_columns(query, db_model, columns)
        
        data_obj = query.all()

        if not data_obj:
            message = "No data found"
        if columns:
            data_obj = [serialize_row(row) for row in data_obj]

        response_obj = response(message, 1, 200, data_obj)

    except Exception as e:
        response_obj = response(str(e), 0, 500)

    return response_obj


async def get_single(db_model, db, id, level=False, columns=None):
    try:
        filter_condition = db_model.user_id if level else db_model.id
        query = db.query(db_model).filter(filter_condition == id)

        if columns:
            # Ensure the columns are ORM mapped attributes
            column_attributes = [getattr(db_model, column) for column in columns]
            query = query.options(load_only(*column_attributes))

        data_obj = query.first()
        if hasattr(data_obj, 'dob'):
            data_obj.dob= data_obj.dob.strftime("%d-%m-%Y")

        if not data_obj:
            message = "Data not found"
            response_obj = response(message, 0, 404)
        else:
            response_obj = response("Data found", 1, 200, data_obj)

    except (ValidationError, Exception) as exc:
        response_obj = response(str(exc), 0, 500)

    return response_obj


async def create_new(model_input, db_model, db, message):
    try:
        data_obj = db_model.from_orm(model_input)
        db.add(data_obj)
        db.commit()
        db.refresh(data_obj)
        response_obj = response(message, 1, 201, data_obj)

    except (ValidationError, Exception) as exc:
        response_obj = response(str(exc), 0, 400)

    return response_obj


async def update_single(item_id, model_input, db_model, db, message, level=False):
    try:
        filter_condition = db_model.user_id if level else db_model.id
        db_item = db.query(db_model).filter(filter_condition == item_id).first()

        if not db_item:
            message = "Item not found"
            return response(message, 404, 0)
        
        if isinstance(model_input, dict):
            input_data = model_input
        else:
            input_data = model_input.dict(exclude_unset=True)
        input_data["modified_at"]= datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        for key, value in input_data.items():
            setattr(db_item, key, value)

        db.commit()
        db.refresh(db_item)
        response_obj = response(message, 1, 200, db_item)

    except (ValidationError, Exception) as exc:
        response_obj = response(str(exc), 0, 400)

    return response_obj


async def delete(item_id, db_model, db):
    try:
        db_item = db.query(db_model).filter(db_model.id == item_id).first()

        if not db_item:
            message = "Item not found"
            return response(message, 404, 0)

        db.delete(db_item)
        db.commit()
        response_obj = response(message, 1, 200)

    except (ValidationError, Exception) as exc:
        response_obj = response(str(exc), 0, 400)

    return response_obj
