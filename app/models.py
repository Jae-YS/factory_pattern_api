from datetime import date
from typing import List
from sqlalchemy import Integer, String, Float, Date, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from .extensions import db


# Base model
class Base(DeclarativeBase):
    pass


# Association Table as a Full Model
class ServiceAssignment(db.Model):
    __tablename__ = "service_assignment"

    service_ticket_id: Mapped[int] = mapped_column(
        ForeignKey("service_tickets.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )
    mechanic_id: Mapped[int] = mapped_column(
        ForeignKey("mechanics.id", ondelete="CASCADE", onupdate="CASCADE"),
        primary_key=True,
    )

    date_assigned: Mapped[date] = mapped_column(Date, nullable=True)

    service_ticket: Mapped["ServiceTicket"] = relationship(
        "ServiceTicket", back_populates="service_assignments"
    )
    mechanic: Mapped["Mechanic"] = relationship(
        "Mechanic", back_populates="service_assignments"
    )


# Models
class Mechanic(db.Model):
    __tablename__ = "mechanics"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    salary: Mapped[float] = mapped_column(Float, nullable=False)
    password = db.Column(db.String(128), nullable=False)

    service_assignments: Mapped[List["ServiceAssignment"]] = relationship(
        "ServiceAssignment", back_populates="mechanic", cascade="all, delete-orphan"
    )
    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        "ServiceTicket",
        secondary="service_assignment",
        back_populates="mechanics",
        viewonly=True,
    )


class Customer(db.Model):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(primary_key=True)
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    email: Mapped[str] = mapped_column(String(360), nullable=False, unique=True)
    phone: Mapped[str] = mapped_column(String(20), nullable=False)
    address: Mapped[str] = mapped_column(String(255), nullable=False)

    service_tickets: Mapped[List["ServiceTicket"]] = relationship(
        "ServiceTicket", back_populates="customer", cascade="all, delete-orphan"
    )


class ServiceTicket(db.Model):
    __tablename__ = "service_tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    service_date: Mapped[date] = mapped_column(Date, nullable=False)
    vin: Mapped[str] = mapped_column(String(17), nullable=False)
    description: Mapped[str] = mapped_column(String(255), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False)
    cost: Mapped[float] = mapped_column(Float, nullable=False)
    date_created: Mapped[date] = mapped_column(Date, nullable=False)

    customer_id: Mapped[int] = mapped_column(
        ForeignKey("customers.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    customer: Mapped["Customer"] = relationship(
        "Customer", back_populates="service_tickets"
    )

    service_assignments: Mapped[List["ServiceAssignment"]] = relationship(
        "ServiceAssignment",
        back_populates="service_ticket",
        cascade="all, delete-orphan",
    )
    mechanics: Mapped[List["Mechanic"]] = relationship(
        "Mechanic",
        secondary="service_assignment",
        back_populates="service_tickets",
        viewonly=True,
    )


class Inventory(db.Model):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    part_name: Mapped[str] = mapped_column(String(255), nullable=False)
    price: Mapped[float] = mapped_column(Float, nullable=False)


class InventoryServiceTicket(db.Model):
    __tablename__ = "inventory_service_tickets"

    id: Mapped[int] = mapped_column(primary_key=True, unique=True)
    service_ticket_id: Mapped[int] = mapped_column(
        ForeignKey("service_tickets.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    inventory_id: Mapped[int] = mapped_column(
        ForeignKey("inventory.id", ondelete="CASCADE", onupdate="CASCADE"),
        nullable=False,
    )
    quantity: Mapped[int] = mapped_column(Integer, nullable=False, default=1)

    service_ticket: Mapped["ServiceTicket"] = relationship("ServiceTicket")
    inventory: Mapped["Inventory"] = relationship("Inventory")
