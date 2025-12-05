from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import json

db = SQLAlchemy()


class Employee(db.Model):
    __tablename__ = "employees"

    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(255))
    email = db.Column(db.String(255))
    phone = db.Column(db.String(20))
    department = db.Column(db.String(255))
    designation = db.Column(db.String(255))
    password_hash = db.Column(db.String(255))
    face_encoding = db.Column(db.Text)
    leave_balance = db.Column(db.Integer, default=0)
    total_leaves = db.Column(db.Integer, default=0)
    remaining_leaves = db.Column(db.Integer, default=0)
    extra_leaves = db.Column(db.Integer, default=0)
    is_active = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.now)

    def set_encoding(self, encoding):
        self.face_encoding = json.dumps(encoding.tolist())

    def get_encoding(self):
        if not self.face_encoding:
            return None
        return json.loads(self.face_encoding)


class Attendance(db.Model):
    __tablename__ = "attendance"

    id = db.Column(db.Integer, primary_key=True)
    employee_id = db.Column(db.Integer, nullable=False)
    in_date = db.Column(db.Date, nullable=False)
    in_time = db.Column(db.DateTime, default=None)
    out_time = db.Column(db.DateTime, default=None)
    latitude = db.Column(db.Float, nullable=True)
    longitude = db.Column(db.Float, nullable=True)
    method = db.Column(db.String(20))
    match_distance = db.Column(db.Float)
    created_at = db.Column(db.DateTime, default=datetime.now)


class AdminUser(db.Model):
    __tablename__ = "admin_users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.now)


# class LeaveRequest(db.Model):
#     __tablename__ = "leave_requests"

#     id = db.Column(db.Integer, primary_key=True)
#     emp_id = db.Column(db.String(50), nullable=False)
#     start_date = db.Column(db.Date, nullable=False)
#     end_date = db.Column(db.Date, nullable=False)
#     reason = db.Column(db.Text)
#     status = db.Column(db.String(20), default="Pending")
#     created_at = db.Column(db.DateTime, default=datetime.now)


class LeaveRequest(db.Model):
    __tablename__ = "leave_requests"

    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(50), db.ForeignKey("employees.emp_id"))
    start_date = db.Column(db.String(20))
    end_date = db.Column(db.String(20))
    reason = db.Column(db.String(255))
    status = db.Column(db.String(20), default="Pending")

    applied_at = db.Column(db.DateTime, default=datetime.utcnow)
    approved_at = db.Column(db.DateTime)
    approved_by = db.Column(db.String(50))
    total_days = db.Column(db.Integer, default=0)
    is_deleted = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.now)


class LeaveBalance(db.Model):
    __tablename__ = "leave_balance"

    id = db.Column(db.Integer, primary_key=True)
    emp_id = db.Column(db.String(50), nullable=False)
    total_leaves = db.Column(db.Integer, default=0)
    used_leaves = db.Column(db.Integer, default=0)
    remaining_leaves = db.Column(db.Integer, default=0)
    extra_leaves = db.Column(db.Integer, default=0)
    updated_at = db.Column(db.DateTime, default=datetime.now, onupdate=datetime.now)

    def update_balance(self):
        self.remaining_leaves = self.total_leaves - self.used_leaves
