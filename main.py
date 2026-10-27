from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from database import get_connection

app = FastAPI(title="Employee Management System")


# Employee data model
class Employee(BaseModel):
    name: str
    email: EmailStr
    department: str
    salary: float


# Home endpoint
@app.get("/")
def home():
    return {"message": "Employee Management System API is running"}

# READ: Get employees with search, filtering, and pagination
@app.get("/employees")
def get_employees(
    search: str = "",
    department: str = "",
    limit: int = 10,
    offset: int = 0
):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="Limit must be between 1 and 100"
        )

    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="Offset cannot be negative"
        )

    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        query = """
            SELECT * FROM employees
            WHERE name LIKE %s
            AND department LIKE %s
            ORDER BY id
            LIMIT %s OFFSET %s
        """

        values = (
            f"%{search}%",
            f"%{department}%",
            limit,
            offset
        )

        cursor.execute(query, values)
        employees = cursor.fetchall()

        return employees

    finally:
        cursor.close()
        connection.close()
        
# READ: Get one employee
@app.get("/employees/{employee_id}")
def get_employee(employee_id: int):
    connection = get_connection()
    cursor = connection.cursor(dictionary=True)

    try:
        cursor.execute(
            "SELECT * FROM employees WHERE id = %s",
            (employee_id,)
        )
        employee = cursor.fetchone()

        if employee is None:
            raise HTTPException(status_code=404, detail="Employee not found")

        return employee

    finally:
        cursor.close()
        connection.close()


# CREATE: Add an employee
@app.post("/employees", status_code=201)
def create_employee(employee: Employee):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
            INSERT INTO employees (name, email, department, salary)
            VALUES (%s, %s, %s, %s)
        """
        values = (
            employee.name,
            str(employee.email),
            employee.department,
            employee.salary
        )

        cursor.execute(query, values)
        connection.commit()

        return {
            "message": "Employee created successfully",
            "id": cursor.lastrowid
        }

    except Exception as error:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(error))

    finally:
        cursor.close()
        connection.close()


# UPDATE: Update an employee
@app.put("/employees/{employee_id}")
def update_employee(employee_id: int, employee: Employee):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        query = """
            UPDATE employees
            SET name = %s, email = %s, department = %s, salary = %s
            WHERE id = %s
        """
        values = (
            employee.name,
            str(employee.email),
            employee.department,
            employee.salary,
            employee_id
        )

        cursor.execute(query, values)

        if cursor.rowcount == 0:
            connection.rollback()

            check_cursor = connection.cursor()
            check_cursor.execute(
                "SELECT id FROM employees WHERE id = %s",
                (employee_id,)
            )
            exists = check_cursor.fetchone()
            check_cursor.close()

            if exists is None:
                raise HTTPException(
                    status_code=404,
                    detail="Employee not found"
                )

            return {"message": "Employee details are unchanged"}

        connection.commit()
        return {"message": "Employee updated successfully"}

    except HTTPException:
        raise

    except Exception as error:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(error))

    finally:
        cursor.close()
        connection.close()


# DELETE: Delete an employee
@app.delete("/employees/{employee_id}")
def delete_employee(employee_id: int):
    connection = get_connection()
    cursor = connection.cursor()

    try:
        cursor.execute(
            "DELETE FROM employees WHERE id = %s",
            (employee_id,)
        )

        if cursor.rowcount == 0:
            raise HTTPException(status_code=404, detail="Employee not found")

        connection.commit()
        return {"message": "Employee deleted successfully"}

    except HTTPException:
        raise

    except Exception as error:
        connection.rollback()
        raise HTTPException(status_code=400, detail=str(error))

    finally:
        cursor.close()
        connection.close()