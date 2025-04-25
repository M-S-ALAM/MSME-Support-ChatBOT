from sqlalchemy import Column, Integer, String, Date, ForeignKey, Enum, Float, DateTime, Table
from sqlalchemy.orm import relationship
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


Base = declarative_base()  # ✅ Ensures correct base class

class Projects(Base):
    __tablename__ = "Projects"  # ✅ Matches actual database table name

    project_id = Column(Integer, primary_key=True, autoincrement=True)
    project_name = Column(String(255), nullable=False)
    customer_id = Column(Integer, ForeignKey("Customer.customer_id"), nullable=False)  # ✅ Correct FK
    employee_id = Column(Integer, ForeignKey("Employee.employee_id"), nullable=False)  # ✅ Correct FK
    start_of_project = Column(Date, nullable=False)
    end_of_project = Column(Date, nullable=False)

    # Define relationships properly
    customer = relationship("Customer", back_populates="projects")
    employee = relationship("Employee", back_populates="projects")


class Customer(Base):
    __tablename__ = "Customer"  # ✅ Matches actual database table name

    customer_id = Column(Integer, primary_key=True, autoincrement=True)
    company_name = Column(String(255), unique=True, nullable=False)
    sector = Column(Enum(
        'manufacturing', 'IT', 'Logistic', 'Finance', 'Healthcare', 'Education',
        'Retail', 'Energy', 'Agriculture', 'Consulting', 'Real Estate',
        'Telecommunications', 'Entertainment'
    ), nullable=False, default='IT')  # ✅ Corrected ENUM

    projects = relationship("Projects", back_populates="customer")


class Employee(Base):
    __tablename__ = 'Employee'
    employee_id = Column(Integer, primary_key=True, autoincrement=True)
    employee_name = Column(String(255), nullable=False, unique=True)
    employee_position = Column(String(255))
    projects = relationship("Projects", back_populates="employee")



#
# from sqlalchemy import create_engine, Column, Integer, String, ForeignKey, Date, DateTime, Text, DECIMAL, Enum
# from sqlalchemy.ext.declarative import declarative_base
# from sqlalchemy.orm import relationship, sessionmaker
#
# Base = declarative_base()
#
# class Department(Base):
#     __tablename__ = 'Department'
#     department_id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), nullable=False)
#
# class Employee(Base):
#     __tablename__ = 'Employee'
#     employee_id = Column(Integer, primary_key=True, autoincrement=True)
#     employee_name = Column(String(255), nullable=False, unique=True)
#     employee_position = Column(String(255))
#     department_id = Column(Integer, ForeignKey('Department.department_id'))
#     department = relationship("Department", back_populates="employees")
#     projects = relationship("Projects", back_populates="employee")
#
# Department.employees = relationship("Employee", order_by=Employee.employee_id, back_populates="department")
#
# class Customer(Base):
#     __tablename__ = 'Customer'
#     customer_id = Column(Integer, primary_key=True, autoincrement=True)
#     company_name = Column(String(255), nullable=False, unique=True)
#     sector = Column(Enum('manufacturing', 'IT', 'Logistic', 'Finance', 'Healthcare', 'Education', 'Retail', 'Energy', 'Agriculture', 'Consulting', 'Real Estate', 'Telecommunications', 'Entertainment'), nullable=False, default='IT')
#     contracts = relationship("Contract", back_populates="customer")
#     projects = relationship("Projects", back_populates="customer")
#
# class Contract(Base):
#     __tablename__ = 'Contract'
#     contract_id = Column(Integer, primary_key=True, autoincrement=True)
#     customer_id = Column(Integer, ForeignKey('Customer.customer_id'), nullable=False)
#     details = Column(String(1024), nullable=False)
#     customer = relationship("Customer", back_populates="contracts")
#
# class Projects(Base):
#     __tablename__ = 'Projects'
#     project_id = Column(Integer, primary_key=True, autoincrement=True)
#     project_name = Column(String(255), nullable=False)
#     customer_id = Column(Integer, ForeignKey('Customer.customer_id'), nullable=False)
#     employee_id = Column(Integer, ForeignKey('Employee.employee_id'), nullable=False)
#     start_of_project = Column(Date, nullable=False)
#     end_of_project = Column(Date, nullable=False)
#     customer = relationship("Customer", back_populates="projects")
#     employee = relationship("Employee", back_populates="projects")
#
# class Task(Base):
#     __tablename__ = 'Task'
#     task_id = Column(Integer, primary_key=True, autoincrement=True)
#     project_id = Column(Integer, ForeignKey('Projects.project_id'), nullable=False)
#     description = Column(Text, nullable=False)
#     status = Column(String(255), nullable=False)
#     project = relationship("Projects", back_populates="tasks")
#
# Projects.tasks = relationship("Task", order_by=Task.task_id, back_populates="project")
#
# class Meeting(Base):
#     __tablename__ = 'Meeting'
#     meeting_id = Column(Integer, primary_key=True, autoincrement=True)
#     project_id = Column(Integer, ForeignKey('Projects.project_id'), nullable=False)
#     scheduled_time = Column(DateTime, nullable=False)
#     purpose = Column(Text, nullable=False)
#     project = relationship("Projects", back_populates="meetings")
#
# Projects.meetings = relationship("Meeting", order_by=Meeting.meeting_id, back_populates="project")
#
# class Budget(Base):
#     __tablename__ = 'Budget'
#     budget_id = Column(Integer, primary_key=True, autoincrement=True)
#     project_id = Column(Integer, ForeignKey('Projects.project_id'), nullable=False)
#     amount = Column(DECIMAL(10, 2), nullable=False)
#     details = Column(Text, nullable=False)
#     project = relationship("Projects", back_populates="budget")
#
# Projects.budget = relationship("Budget", uselist=False, back_populates="project")
#
# class Vendor(Base):
#     __tablename__ = 'Vendor'
#     vendor_id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), nullable=False)
#
# class Equipment(Base):
#     __tablename__ = 'Equipment'
#     equipment_id = Column(Integer, primary_key=True, autoincrement=True)
#     name = Column(String(255), nullable=False)
#     type = Column(String(255), nullable=False)
#     vendor_id = Column(Integer, ForeignKey('Vendor.vendor_id'))
#     vendor = relationship("Vendor", back_populates="equipments")
#
# Vendor.equipments = relationship("Equipment", order_by=Equipment.equipment_id, back_populates="vendor")
#
