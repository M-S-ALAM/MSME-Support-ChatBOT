import pandas as pd
import numpy as np
from faker import Faker
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
import pymysql  # Ensure PyMySQL is installed

# Import ORM models
from schema import Base, Projects, Employee, Customer

# Predefined valid sectors for customers
VALID_SECTORS = [
    "Manufacturing", "IT", "Logistics", "Finance", "Healthcare", "Education",
    "Retail", "Energy", "Agriculture", "Consulting", "Real Estate",
    "Telecommunications", "Entertainment"
]

class DataGenerator:
    def __init__(self, engine):
        self.fake = Faker()
        self.engine = engine
        self.Session = sessionmaker(bind=self.engine)
        self.session = self.Session()
        Base.metadata.create_all(self.engine)  # Create all tables if not exist

    def generate_employee_data(self, num_records: int = 100) -> pd.DataFrame:
        data = [{'employee_name': self.fake.name(), 'employee_position': self.fake.job()} for _ in range(num_records)]
        return pd.DataFrame(data)

    def generate_customer_data(self, num_records: int = 100) -> pd.DataFrame:
        data, company_names = [], set()
        while len(data) < num_records:
            company_name = self.fake.company()
            if company_name not in company_names:
                company_names.add(company_name)
                sector = np.random.choice(VALID_SECTORS)
                data.append({'company_name': company_name, 'sector': sector})
        return pd.DataFrame(data)

    def generate_projects_data(self, num_records: int = 100) -> pd.DataFrame:
        customers = self.session.query(Customer.customer_id).all()
        employees = self.session.query(Employee.employee_id).all()
        if not customers or not employees:
            print("⚠️ No customers or employees found.")
            return pd.DataFrame()
        customer_ids = [c.customer_id for c in customers]
        employee_ids = [e.employee_id for e in employees]
        data = []
        for _ in range(num_records):
            start_date = self.fake.date_between(start_date="-2y", end_date="-1y")
            end_date = self.fake.date_between(start_date=start_date, end_date="today")
            data.append({
                "project_name": self.fake.word(),
                "customer_id": np.random.choice(customer_ids),
                "employee_id": np.random.choice(employee_ids),
                "start_of_project": start_date,
                "end_of_project": end_date,
            })
        return pd.DataFrame(data)

    def insert_data(self, model, data: pd.DataFrame):
        if data.empty:
            print(f"⚠️ No data to insert for {model.__tablename__}.")
            return

        for row in data.to_dict(orient='records'):
            try:
                obj = model(**row)
                self.session.add(obj)
                self.session.commit()
                print(f"✅ Inserted: {row}")
            except IntegrityError as e:
                self.session.rollback()
                print(f"⚠️ Skipping duplicate entry: {row} due to {e}")

        print(f"✅ Finished inserting into {model.__tablename__}.")

    def close_connection(self):
        self.session.close()
        print("🔌 Database connection closed.")

def main():
    db_user = "shobot"
    db_password = "shobot"
    db_host = "localhost"
    db_name = "walmart_chatbot_dummy"
    engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")
    db_generator = DataGenerator(engine)
    db_generator.insert_data(Employee, db_generator.generate_employee_data())
    db_generator.insert_data(Customer, db_generator.generate_customer_data())
    project_data = db_generator.generate_projects_data()
    if not project_data.empty:
        db_generator.insert_data(Projects, project_data)
    db_generator.close_connection()

if __name__ == "__main__":
    main()

#
#
# import pandas as pd
# import numpy as np
# import random
# from faker import Faker
# from sqlalchemy import create_engine
# from sqlalchemy.orm import sessionmaker
# from sqlalchemy.exc import IntegrityError
# import pymysql  # Ensure PyMySQL is installed
# from datetime import datetime
#
# # Import ORM models
# from schema import Base, Projects, Employee, Customer, Vendor, Budget, Meeting, Department, Contract, Task, Equipment
#
# # Predefined valid sectors for customers
# VALID_SECTORS = [
#     "Manufacturing", "IT", "Logistics", "Finance", "Healthcare", "Education",
#     "Retail", "Energy", "Agriculture", "Consulting", "Real Estate",
#     "Telecommunications", "Entertainment"
# ]
#
#
# class DataGenerator:
#     """
#     A class to generate and insert synthetic data for Employees, Customers, and Projects
#     into a MySQL database using SQLAlchemy.
#     """
#
#     def __init__(self, engine):
#         """Initialize the DataGenerator with a database engine."""
#         self.fake = Faker()
#         self.engine = engine
#         self.Session = sessionmaker(bind=self.engine)
#         self.session = self.Session()
#
#         # Ensure all tables are created before inserting data
#         Base.metadata.create_all(self.engine)
#
#     def generate_employee_data(self, num_records: int = 1000) -> pd.DataFrame:
#         """Generate random employee data."""
#         data = [
#             {"employee_name": self.fake.name(), "employee_position": self.fake.job()}
#             for _ in range(num_records)
#         ]
#         return pd.DataFrame(data)
#
#     def generate_customer_data(self, num_records: int = 1000) -> pd.DataFrame:
#         """Generate unique customer data."""
#         data, company_names = [], set()
#
#         while len(data) < num_records:
#             company_name = self.fake.company()
#             if company_name not in company_names:
#                 company_names.add(company_name)
#                 sector = str(np.random.choice(VALID_SECTORS))[:50]  # Ensure sector fits column size
#                 data.append({"company_name": company_name, "sector": sector})
#
#         return pd.DataFrame(data)
#
#     def generate_projects_data(self, num_records: int = 1000) -> pd.DataFrame:
#         """Generate random project data with valid Customer and Employee IDs."""
#         customers = self.session.query(Customer.customer_id).all()
#         employees = self.session.query(Employee.employee_id).all()
#
#         if not customers or not employees:
#             print("⚠️ Cannot generate projects: No customers or employees found.")
#             return pd.DataFrame()
#
#         customer_ids = [c.customer_id for c in customers]
#         employee_ids = [e.employee_id for e in employees]
#
#         data = []
#         for _ in range(num_records):
#             start_date = self.fake.date_between(start_date="-2y", end_date="-1y")
#             end_date = self.fake.date_between(start_date=start_date, end_date="today")
#
#             data.append({
#                 "project_name": self.fake.word(),
#                 "customer_id": np.random.choice(customer_ids),
#                 "employee_id": np.random.choice(employee_ids),
#                 "start_of_project": start_date,
#                 "end_of_project": end_date,
#             })
#
#         return pd.DataFrame(data)
#
#     def generate_department_data(self, num_records: int = 1000) -> pd.DataFrame:
#         """Generate random department data."""
#         data = [
#             {"name": self.fake.company_suffix() + " Department"}  # Adding 'Department' to make it clear
#             for _ in range(num_records)
#         ]
#         return pd.DataFrame(data)
#
#     def generate_contract_data(self, num_records: int = 1000):
#         """Generate random contract data with valid Customer IDs."""
#         customers = self.session.query(Customer.customer_id).all()
#
#         if not customers:
#             print("⚠️ Cannot generate contracts: No customers found.")
#             return pd.DataFrame()
#
#         customer_ids = [c.customer_id for c in customers]
#
#         data = []
#         for _ in range(num_records):
#             details = self.fake.paragraph(nb_sentences=3)
#             customer_id = random.choice(customer_ids)
#
#             data.append({
#                 "customer_id": customer_id,
#                 "details": details
#             })
#
#         return pd.DataFrame(data)
#
#     def generate_task_data(self, num_records: int = 1000):
#         """Generate random task data with valid Project IDs."""
#         projects = self.session.query(Projects.project_id).all()
#
#         if not projects:
#             print("⚠️ Cannot generate tasks: No projects found.")
#             return pd.DataFrame()
#
#         project_ids = [p.project_id for p in projects]
#
#         data = []
#         for _ in range(num_records):
#             description = self.fake.sentence(nb_words=6)  # Generate a fake task description
#             status = random.choice(['Pending', 'Completed', 'In Progress'])  # Randomly assign a status
#             project_id = random.choice(project_ids)  # Randomly select a project ID from provided list
#
#             data.append({
#                 "project_id": project_id,
#                 "description": description,
#                 "status": status
#             })
#
#         return pd.DataFrame(data)
#
#     def generate_meeting_data(self, num_records=1000):
#         """Generate data for Meeting instances."""
#         projects = self.session.query(Projects.project_id).all()
#         if not projects:
#             print("⚠️ Cannot generate meetings: No projects found.")
#             return pd.DataFrame()
#
#         project_ids = [p.project_id for p in projects]
#         data = [{
#             'project_id': random.choice(project_ids),
#             'scheduled_time': self.fake.date_time_between(start_date='-1y', end_date='now'),
#             'purpose': self.fake.sentence(nb_words=10)
#         } for _ in range(num_records)]
#
#         return pd.DataFrame(data)
#
#     def generate_budget_data(self, num_records=1000):
#         """Generate data for Budget instances."""
#         projects = self.session.query(Projects.project_id).all()
#         if not projects:
#             print("⚠️ Cannot generate budgets: No projects found.")
#             return pd.DataFrame()
#
#         project_ids = [p.project_id for p in projects]
#         data = [{
#             'project_id': random.choice(project_ids),
#             'amount': round(random.uniform(1000.0, 50000.0), 2),
#             'details': self.fake.sentence(nb_words=15)
#         } for _ in range(num_records)]
#
#         return pd.DataFrame(data)
#
#     def generate_vendor_data(self, num_records=1000):
#         """Generate data for Vendor instances."""
#         data = [{
#             'name': self.fake.company()
#         } for _ in range(num_records)]
#
#         return pd.DataFrame(data)
#
#     def generate_equipment_data(self, num_records=1000):
#         """Generate data for Equipment instances."""
#         vendors = self.session.query(Vendor.vendor_id).all()
#         if not vendors:
#             print("⚠️ Cannot generate equipment: No vendors found.")
#             return pd.DataFrame()
#
#         vendor_ids = [v.vendor_id for v in vendors]
#         data = [{
#             'name': self.fake.word(),
#             'type': self.fake.word(),
#             'vendor_id': random.choice(vendor_ids)
#         } for _ in range(num_records)]
#
#         return pd.DataFrame(data)
#
#
#
#     def insert_data(self, model, data: pd.DataFrame):
#         """Insert generated data into the database while avoiding duplicates."""
#         if data.empty:
#             print(f"⚠️ No data to insert for {model.__tablename__}.")
#             return
#
#         for row in data.to_dict(orient="records"):
#             try:
#                 obj = model(**row)
#                 self.session.add(obj)
#                 self.session.commit()
#                 print(f"✅ Inserted: {row}")
#             except IntegrityError:
#                 self.session.rollback()
#                 print(f"⚠️ Skipping duplicate entry: {row}")
#
#         print(f"✅ Finished inserting into {model.__tablename__}.")
#
#     def close_connection(self):
#         """Close the database session."""
#         self.session.close()
#         print("🔌 Database connection closed.")
#
#
# def main():
#     """Main function to generate and insert data into the database."""
#     db_user = "shobot"
#     db_password = "shobot"
#     db_host = "localhost"
#     db_name = "walmart_chatbot_dummy"
#
#     # Create the database engine
#     engine = create_engine(f"mysql+pymysql://{db_user}:{db_password}@{db_host}/{db_name}")
#
#     # Initialize data generator
#     db_generator = DataGenerator(engine)
#
#     # Generate and insert Employee and Customer data
#     db_generator.insert_data(Employee, db_generator.generate_employee_data())
#     db_generator.insert_data(Customer, db_generator.generate_customer_data())
#
#     # Generate and insert Projects only if Customers & Employees exist
#     project_data = db_generator.generate_projects_data()
#     if not project_data.empty:
#         db_generator.insert_data(Projects, project_data)
#
#     # Generate and insert data for Department, Contract, Task, Meeting, Budget, Vendor, and Equipment
#     db_generator.insert_data(Department, db_generator.generate_department_data())
#     contract_data = db_generator.generate_contract_data()
#     if not contract_data.empty:
#         db_generator.insert_data(Contract, contract_data)
#     db_generator.insert_data(Task, db_generator.generate_task_data())
#     db_generator.insert_data(Meeting, db_generator.generate_meeting_data())
#     db_generator.insert_data(Budget, db_generator.generate_budget_data())
#     vendor_data = db_generator.generate_vendor_data()
#     if not vendor_data.empty:
#         db_generator.insert_data(Vendor, vendor_data)
#     equipment_data = db_generator.generate_equipment_data()
#     if not equipment_data.empty:
#         db_generator.insert_data(Equipment, equipment_data)
#
#     # Closing session
#     db_generator.close_connection()
#
# if __name__ == "__main__":
#     main()
#
#
#
#
