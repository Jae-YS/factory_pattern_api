from datetime import date
from typing import List
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from .extensions import db


# Base model
class Base(DeclarativeBase):
    pass


# Association Table
service_assignment = db.Table(
    "service_assignment",
    db.Column(
        "service_ticket_id",
        db.Integer,
        db.ForeignKey("service_tickets.id"),
        primary_key=True,
    ),
    db.Column(
        "mechanic_id", db.Integer, db.ForeignKey("mechanics.id"), primary_key=True
    ),
)


# Models
class Mechanic(db.Model):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    address: Mapped[str] = mapped_column(db.String(255), nullable=False)
    salary: Mapped[float] = mapped_column(db.Float, nullable=False)

    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        "ServiceTicket",
        secondary=service_assignment,
        back_populates="mechanics",
    )


class Customer(db.Model):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(db.String(255), nullable=False)
    email: Mapped[str] = mapped_column(db.String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(db.String(20), nullable=False)
    address: Mapped[str] = mapped_column(db.String(255), nullable=False)

    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        "ServiceTicket", back_populates="customer"
    )


class ServiceTicket(db.Model):
    __tablename__ = "service_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_date: Mapped[date] = mapped_column(db.Date, nullable=False)
    vin: Mapped[str] = mapped_column(db.String(17), nullable=False)
    description: Mapped[str] = mapped_column(db.String(255), nullable=False)
    status: Mapped[str] = mapped_column(db.String(50), nullable=False)
    cost: Mapped[float] = mapped_column(db.Float, nullable=False)
    date_created: Mapped[date] = mapped_column(db.Date, nullable=False)

    customer_id: Mapped[int] = mapped_column(
        db.Integer, db.ForeignKey("customers.id"), nullable=False
    )
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="service_tickets"
    )
    mechanics: Mapped[List["Mechanic"]] = relationship(
        "Mechanic",
        secondary=service_assignment,
        back_populates="service_tickets",
    )
