import calendar
import hashlib
import cv2
import face_recognition
import flask
import base64
from PIL import Image
import numpy as np
import io
from io import BytesIO
import json

# from flask.cor import WTF
from flask import Flask, request, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime, date, timedelta
from models.models import (
    db,
    Employee,
    Attendance,
    AdminUser,
    LeaveRequest,
    LeaveBalance,
)
from utils.utils import decode_base64_image, get_face_encoding, compare_encodings
from config.config import Config

app = Flask(__name__)
app.config.from_object(Config)
db.init_app(app)


@app.route("/")
def home():
    return "Face Attendance API Running!"


# ---------------------------
# REGISTER EMPLOYEE
# ---------------------------
@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()

    name = data.get("name")
    photo = data.get("photo")

    if not name or not photo:
        return jsonify({"error": "Name or photo missing"}), 400

    image = decode_base64_image(photo)
    # encoding = get_face_encoding(image)
    if image is None:
        return {"error": "Invalid image"}, 400

    rgb_image = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)

    encodings = face_recognition.face_encodings(rgb_image)

    if len(encodings) == 0:
        return {"error": "No face detected"}, 400

    encoding = encodings[0]

    if encoding is None:
        return jsonify({"error": "No face detected"}), 400

    emp = Employee(name=name)
    emp.set_encoding(encoding)

    db.session.add(emp)
    db.session.commit()

    return jsonify({"message": "Candidate Registered"})


# ---------------------------
# Employee Login
# ---------------------------

""" 
Url:http://127.0.0.1:5000/emp-login
Emplotee Login Feature The Employee Can log in using its employee id and Hashed password provided by the HR, or Admin and in response it returns the `{
  "empId": "4",
  "name": "John Doe",
  "userId": 1
}`
"""


@app.route("/emp-login", methods=["POST"])
def emp_login():
    data = request.get_json()

    employee_id = data.get("employeeId")
    password = data.get("password")

    if not employee_id or not password:
        return jsonify({"empId": "", "name": "", "userId": 0}), 200

    password_hash = hashlib.md5(password.encode()).hexdigest()

    employee = Employee.query.filter_by(emp_id=employee_id).first()

    if not employee:
        return jsonify({"empId": "", "name": "", "userId": 0}), 200

    if password_hash != password_hash:
        return jsonify({"empId": "", "name": "", "userId": 0}), 200

    return (
        jsonify(
            {"empId": employee.emp_id, "name": employee.name, "userId": employee.id}
        ),
        200,
    )


""" 
Admin Login Feature :
url:http://127.0.0.1:5000/login

"""
# ---------------------------
# Admin Login
# ---------------------------


@app.route("/login", methods=["POST"])
def admin_login():
    print("ADMIN LOGIN ENDPOINT IS RUNNING")
    data = request.get_json()

    email = data.get("email")
    password = data.get("password")

    print(">> EMAIL RECEIVED:", email)
    print(">> PASSWORD RECEIVED RAW:", password)

    if not email or not password:
        return jsonify({"email": "", "message": "", "userId": 0}), 200

    password_hash = hashlib.md5(password.encode()).hexdigest()
    print(">> PASSWORD RECEIVED HASH:", password_hash)

    admin = AdminUser.query.filter_by(email=email).first()

    if not admin:
        return jsonify({"email": "", "message": "", "userId": 0}), 200

    if admin.password_hash != password_hash:
        return jsonify({"email": "", "message": "", "userId": 0}), 200

    return (
        jsonify(
            {"email": admin.email, "message": "Login Successful", "userId": admin.id}
        ),
        200,
    )


# ---------------------------
# Admin change password
# ---------------------------

""" 
URL:http://127.0.0.1:5000/api/admin/change-password
With this feature we can change the password of the Admin 
"""


@app.route("/api/admin/change-password", methods=["POST"])
def admin_change_password():
    data = request.get_json()

    userId = data.get("userId")
    current_password = data.get("currentPassword")
    new_password = data.get("newPassword")

    if not userId or not current_password or not new_password:
        return jsonify({"message": "Missing Required Field Details"}), 200

    admin = AdminUser.query.filter_by(id=userId).first()

    if not admin:
        return jsonify({"message": "User not found"}), 200

    if admin.password_hash != current_password:
        return jsonify({"message": "Invalid current password"}), 200

    admin.password_hash = new_password
    db.session.commit()

    return jsonify({"message": "password changed successfully"}), 200


# ---------------------------
# Employee change password
# ---------------------------

""" 
URL:http://127.0.0.1:5000/api/employee/change-password
With this feature we can change the password of the Employee 
"""


@app.route("/api/employee/change-password", methods=["POST"])
def employee_change_password():
    data = request.get_json()

    empId = data.get("empId")
    current_password = data.get("currentPassword")
    new_password = data.get("newPassword")

    if not empId or not current_password or not new_password:
        return jsonify({"message": "Missing Required Field Details "}), 200

    employee = Employee.query.filter_by(emp_id=empId).first()

    if not employee:
        return jsonify({"message": "Employee not found"}), 200

    if employee.password_hash != current_password:
        return jsonify({"message": "Invalid Current password"}), 200

    employee.password_hash = new_password
    db.session.commit()

    return jsonify({"message": "Password changed successfully"}), 200


# ---------------------------
# Employee change password
# ---------------------------

""" 
URL:http://127.0.0.1:5000/api/register 
With this feature we can change the password of the Employee 
"""


@app.route("/api/register", methods=["POST"])
def register_employee():
    data = request.get_json()

    emp_id = data.get("emp_id")
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    department = data.get("department")
    designation = data.get("designation")
    password = data.get("password")
    user_id = data.get("userId")

    if (
        not emp_id
        or not name
        or not email
        or not phone
        or not department
        or not designation
        or not password
    ):
        return jsonify({"message": "Missing Required Field"}), 200

    existing = Employee.query.filter_by(emp_id=emp_id).first()

    if existing:
        return jsonify({"message": "Employee already exists"}), 400

    password_hash = hashlib.md5(password.encode()).hexdigest()

    new_emp = Employee(
        emp_id=emp_id,
        name=name,
        email=email,
        phone=phone,
        department=department,
        designation=designation,
        password_hash=password_hash,
    )

    db.session.add(new_emp)
    db.session.commit()

    leave_balance = LeaveBalance(
        emp_id=emp_id, total_leaves=10, remaining_leaves=10, extra_leaves=0
    )
    db.session.add(leave_balance)
    db.session.commit()

    return jsonify({"message": "Employee registerd successfully"}), 200


# ---------------------------
# Update Face
# ---------------------------

""" 
URL:http://127.0.0.1:5000/update-face
With this feature we can change,update  the face.
"""


@app.route("/update-face", methods=["POST"])
def update_face():
    data = request.get_json()

    user_id = data.get("user_id")
    emp_id = data.get("emp_id")
    photo = data.get("photo")

    # Validate input
    if not user_id or not emp_id or not photo:
        return jsonify({"message": "Missing required fields"}), 400

    # Fetch employee by user_id
    employee = Employee.query.filter_by(id=user_id).first()

    if not employee:
        return jsonify({"message": "User not found"}), 400

    # Check emp_id matches
    if employee.emp_id != emp_id:
        return jsonify({"message": "Employee ID does not match"}), 400

    # Decode base64 → image
    try:
        # Remove metadata (if exists)
        if "base64," in photo:
            photo = photo.split("base64,")[1]

        image_bytes = base64.b64decode(photo)
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")

    except Exception as e:
        print("Decode error:", e)
        return jsonify({"message": "Invalid image"}), 400

    # Detect face & encode
    image_array = np.array(image)
    face_locations = face_recognition.face_locations(image_array)

    if len(face_locations) == 0:
        return jsonify({"message": "No face detected"}), 400

    face_encoding = face_recognition.face_encodings(image_array, face_locations)[0]

    # Save encoding to DB
    employee.face_encoding = json.dumps(face_encoding.tolist())
    db.session.commit()

    return jsonify({"message": "Face updated successfully"}), 200


# ---------------------------
# Employee Update Face
# ---------------------------

""" 
URL:http://127.0.0.1:5000/emp-update-face
With this feature we can  change,update the face of the employee even without user_id only using employee id.
"""


@app.route("/emp-update-face", methods=["POST"])
def employee_update_face():
    data = request.get_json()

    emp_id = data.get("emp_id")
    photo_base64 = data.get("photo")

    if not emp_id or not photo_base64:
        return jsonify({"message": "Missing required fields"}), 400

    employee = Employee.query.filter_by(emp_id=emp_id).first()

    if not employee:
        return jsonify({"message": "Employee not found"}), 400

    try:
        # Remove metadata if present (e.g., data:image/jpeg;base64,)
        if "," in photo_base64:
            photo_base64 = photo_base64.split(",")[1]

        image_data = base64.b64decode(photo_base64)
        image = Image.open(io.BytesIO(image_data))

        image = image.convert("RGB")

        image_np = np.array(image)

        encodings = face_recognition.face_encodings(image_np)

        if len(encodings) == 0:
            return jsonify({"message": "No face detected"}), 400

        face_encoding = encodings[0]

        employee.set_encoding(face_encoding)
        db.session.commit()

        return jsonify({"message": "Face updated successfully"})

    except Exception as e:
        return jsonify({"message": str(e)}), 400


@app.route("/attendance", methods=["POST"])
def attendance():
    data = request.get_json()
    photo_base64 = data.get("photo")

    if not photo_base64:
        return jsonify({"error": "Missing photo"}), 400

    try:
        # Remove "data:image/jpeg;base64," if present
        if "," in photo_base64:
            photo_base64 = photo_base64.split(",")[1]

        # Decode Base64 → image
        image_data = base64.b64decode(photo_base64)
        image = Image.open(BytesIO(image_data)).convert("RGB")
        np_img = np.array(image)

        # Face detection
        encodings = face_recognition.face_encodings(np_img)
        if len(encodings) == 0:
            return jsonify({"error": "No face detected"}), 500

        input_face = encodings[0]

        # Compare with employees
        employees = Employee.query.all()
        matched_emp = None
        min_dist = 0.6  # threshold

        for emp in employees:
            if emp.face_encoding:
                stored_enc = np.array(json.loads(emp.face_encoding))
                dist = np.linalg.norm(stored_enc - input_face)

                if dist < min_dist:
                    matched_emp = emp
                    min_dist = dist

        if not matched_emp:
            return jsonify({"error": "No matching employee found"}), 500

        today = date.today()

        # Check if employee already marked attendance today
        attendance_record = Attendance.query.filter_by(
            employee_id=matched_emp.id, in_date=today
        ).first()

        now = datetime.now()

        if attendance_record:
            # Already checked in → UPDATE OUT TIME
            attendance_record.out_time = now
            attendance_record.match_distance = min_dist
            db.session.commit()

            return (
                jsonify(
                    {
                        "message": "Attendance OUT updated",
                        "employee_id": matched_emp.id,
                        "emp_id": matched_emp.emp_id,
                        "name": matched_emp.name,
                        "distance": min_dist,
                    }
                ),
                200,
            )

        else:
            # FIRST attendance → create IN TIME record
            new_attendance = Attendance(
                employee_id=matched_emp.id,
                in_date=today,
                in_time=now,
                method="face",
                match_distance=min_dist,
            )

            db.session.add(new_attendance)
            db.session.commit()

            return (
                jsonify(
                    {
                        "message": "Attendance IN marked",
                        "employee_id": matched_emp.id,
                        "emp_id": matched_emp.emp_id,
                        "name": matched_emp.name,
                        "distance": min_dist,
                    }
                ),
                200,
            )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @app.route("/emp-attendance", methods=["POST"])
# def emp_attendance():
#     data = request.get_json()
#     photo_base64 = data.get("photo")

#     if not photo_base64:
#         return jsonify({"error": "No photo provided"}), 400

#     try:
#         # Clean base64 header
#         if "," in photo_base64:
#             photo_base64 = photo_base64.split(",")[1]

#         # Decode base64 → image
#         image_bytes = base64.b64decode(photo_base64)
#         image = Image.open(BytesIO(image_bytes)).convert("RGB")
#         np_img = np.array(image)

#         # Extract face encodings
#         encodings = face_recognition.face_encodings(np_img)
#         if len(encodings) == 0:
#             return jsonify({"error": "No face detected"}), 400

#         input_face = encodings[0]

#         # Compare with employees
#         employees = Employee.query.all()
#         matched_employee = None
#         best_distance = 0.6

#         for emp in employees:
#             if emp.face_encoding:
#                 stored_encoding = np.array(json.loads(emp.face_encoding))
#                 dist = np.linalg.norm(stored_encoding - input_face)

#                 if dist < best_distance:
#                     best_distance = dist
#                     matched_employee = emp

#         if not matched_employee:
#             return jsonify({"error": "Employee not recognized"}), 400

#         # Attendance Logic
#         today = date.today()
#         now = datetime.now()

#         attendance = Attendance.query.filter_by(
#             employee_id=matched_employee.id, in_date=today
#         ).first()

#         if attendance:
#             # Already marked IN → update OUT
#             attendance.out_time = now
#             attendance.match_distance = best_distance
#             db.session.commit()

#             return (
#                 jsonify(
#                     {
#                         "message": "Attendance OUT updated",
#                         "emp_id": matched_employee.emp_id,
#                         "name": matched_employee.name,
#                         "distance": best_distance,
#                     }
#                 ),
#                 200,
#             )

#         else:
#             # FIRST TIME → mark IN
#             new_attendance = Attendance(
#                 employee_id=matched_employee.id,
#                 in_date=today,
#                 in_time=now,
#                 method="face",
#                 match_distance=best_distance,
#             )
#             db.session.add(new_attendance)
#             db.session.commit()

#             return (
#                 jsonify(
#                     {
#                         "message": "Attendance IN marked",
#                         "emp_id": matched_employee.emp_id,
#                         "name": matched_employee.name,
#                         "distance": best_distance,
#                     }
#                 ),
#                 200,
#             )

#     except Exception as e:
#         return jsonify({"error": str(e)}), 500


@app.route("/emp-attendance", methods=["POST"])
def emp_attendance():
    data = request.get_json()

    photo = data.get("photo")
    latitude = data.get("latitude")
    longitude = data.get("longitude")

    if not photo:
        return jsonify({"error": "No photo provided"}), 400

    # Decode and detect face
    img_bytes = base64.b64decode(photo.split(",")[-1])
    img = face_recognition.load_image_file(io.BytesIO(img_bytes))
    encodings = face_recognition.face_encodings(img)

    if len(encodings) == 0:
        return jsonify({"error": "No face detected"}), 400

    input_face = encodings[0]

    # Compare with employee faces
    employees = Employee.query.all()
    for emp in employees:
        if emp.face_encoding:
            known = np.array(json.loads(emp.face_encoding))
            dist = face_recognition.face_distance([known], input_face)[0]

            if dist < 0.45:
                today = date.today()
                attendance = Attendance.query.filter_by(
                    employee_id=emp.id, in_date=today
                ).first()

                # IN TIME
                if not attendance:
                    new_att = Attendance(
                        employee_id=emp.id,
                        in_date=today,
                        in_time=datetime.now(),
                        latitude=latitude,
                        longitude=longitude,
                        method="face",
                        match_distance=float(dist),
                    )
                    db.session.add(new_att)

                # OUT TIME
                else:
                    attendance.out_time = datetime.now()
                    attendance.latitude = latitude
                    attendance.longitude = longitude

                db.session.commit()

                return (
                    jsonify(
                        {
                            "message": "Attendance marked",
                            "employee_id": emp.id,
                            "distance": float(dist),
                        }
                    ),
                    200,
                )

    return jsonify({"error": "No matching face found"}), 400


@app.route("/attendance-status", methods=["POST"])
def attendance_status():
    data = request.get_json()

    user_id = data.get("userId")

    if not user_id:
        return jsonify({"error": "userId is required"}), 400

    # Check if employee exists
    employee = Employee.query.filter_by(id=user_id).first()
    if not employee:
        return jsonify({"error": "Employee not found"}), 404

    today = datetime.now().date()

    # Check today's attendance record
    attendance = Attendance.query.filter_by(employee_id=user_id, in_date=today).first()

    response = {
        "message": "",
        "next_action": "",
        "next_allowed_time": "",
        "next_allowed_timestamp": 0,
        "remaining_hours": 0,
        "remaining_minutes": 0,
        "remaining_seconds": 0,
        "status": "",
    }

    # Case 1 → No attendance yet today
    if not attendance:
        response["status"] = "not_marked"
        response["next_action"] = "mark_in"
        return jsonify(response), 200

    # Case 2 → IN is marked but OUT is not
    if attendance.in_time and not attendance.out_time:
        # You can decide if OUT is allowed after X hours
        ALLOWED_OUT_AFTER_HOURS = 1

        next_allowed = attendance.in_time + timedelta(hours=ALLOWED_OUT_AFTER_HOURS)
        now = datetime.now()

        if now >= next_allowed:
            response["status"] = "in_marked"
            response["next_action"] = "mark_out"
            return jsonify(response), 200
        else:
            # Calculate remaining time
            diff = next_allowed - now
            response["status"] = "wait_for_out"
            response["next_action"] = "mark_out"
            response["next_allowed_time"] = next_allowed.strftime("%Y-%m-%d %H:%M:%S")
            response["next_allowed_timestamp"] = int(next_allowed.timestamp())

            response["remaining_hours"] = diff.seconds // 3600
            response["remaining_minutes"] = (diff.seconds % 3600) // 60
            response["remaining_seconds"] = diff.seconds % 60

            return jsonify(response), 200

    # Case 3 → IN and OUT both marked
    if attendance.in_time and attendance.out_time:
        response["status"] = "completed"
        response["next_action"] = "none"
        return jsonify(response), 200

    return jsonify({"error": "Unknown attendance status"}), 500


@app.route("/get_all_attendance", methods=["POST"])
def get_all_attendance():
    data = request.get_json()

    user_id = data.get("userId")

    if not user_id:
        return jsonify({"error": "Missing userId"}), 400

    try:
        records = Attendance.query.filter_by(employee_id=user_id).all()
        attendance_list = []

        for record in records:
            attendance_list.append(
                {
                    "id": record.id,
                    "employee_id": record.employee_id,
                    "in_date": record.in_date.isoformat(),
                    "in_time": record.in_time.isoformat() if record.in_time else None,
                    "out_time": (
                        record.out_time.isoformat() if record.out_time else None
                    ),
                    "latitude": record.latitude,
                    "longitude": record.longitude,
                    "method": record.method,
                    "match_distance": record.match_distance,
                    "created_at": record.created_at.isoformat(),
                }
            )

        return jsonify({"attendance": attendance_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/get_attendance", methods=["POST"])
def get_attendance_emp_id():
    data = request.get_json()

    emp_id = data.get("emp_id")

    if not emp_id:
        return jsonify({"error": "Missing emp_id"}), 400

    employee = Employee.query.filter_by(emp_id=emp_id).first()
    if not employee:
        return jsonify({"error": "Employee not found"}), 200

    try:
        records = Attendance.query.filter_by(employee_id=employee.id).all()

        attendance_list = []

        for record in records:
            attendance_list.append(
                {
                    "candidate_id": record.employee_id,
                    "id": record.id,
                    "in_date": record.in_date.isoformat(),
                    "in_latitude": record.latitude,
                    "in_longitude": record.longitude,
                    "in_time": record.in_time.isoformat() if record.in_time else "",
                    "out_time": (
                        record.out_time.isoformat() if record.out_time else "None"
                    ),
                }
            )

        return jsonify({"attendance": attendance_list}), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/leave/apply", methods=["POST"])
def apply_leave():
    data = request.get_json()

    emp_id = data.get("emp_id")
    start_date = data.get("start_date")
    end_date = data.get("end_date")
    reason = data.get("reason")

    if not emp_id or not start_date or not end_date or not reason:
        return jsonify({"message": "Missing Required fields"}), 400

    try:
        start = datetime.strptime(start_date, "%Y-%m-%d").date()
        end = datetime.strptime(end_date, "%Y-%m-%d").date()
    except Exception as e:
        return jsonify({"message": "Invalid date format"}), 400

    leave = LeaveRequest(
        emp_id=emp_id, start_date=start, end_date=end, reason=reason, status="Pending"
    )

    db.session.add(leave)
    db.session.commit()

    return jsonify({"message": "Leave applied successfully"}), 201


@app.route("/api/leave/my-requests", methods=["POST"])
def my_leave_requests():
    data = request.get_json()

    emp_id = data.get("emp_id")

    if not emp_id:
        return jsonify({"requests": []}), 200

    leave = (
        LeaveRequest.query.filter_by(emp_id=emp_id)
        .order_by(LeaveRequest.created_at.desc())
        .all()
    )

    result = []

    for leaves in leave:
        result.append(
            {
                "id": leaves.id,
                "start_date": str(leaves.start_date),
                "end_date": str(leaves.end_date),
                "reason": leaves.reason,
                "status": leaves.status,
                "applied_at": leaves.created_at.strftime("%Y-%m-%d %H:%M:%S"),
            }
        )

    return jsonify({"requests": result}), 200


# @app.route("/api/leave/decide",methods=["POST"])
# def decide_leave_requests():
#     data = request.get_json()

#     leave_id = data.get("leave_id")
#     action = data.get("action")
#     admin_id = data.get("admin_id")

#     if not leave_id or not action or not admin_id:
#         return jsonify({"message":"Missing Required Fields"}),200

#     if action not in ["Approved","Rejected"]:
#         return jsonify({"message":"Invalid Action use 'Approved' or 'Rejected'."}),200

#     leave_request = LeaveRequest.query.filter_by(id = leave_id).first()

#     if not leave_request:
#         return jsonify({"message":"Leave Request not found"}),200

#     leave_request.status = action
#     db.session.commit()

#     success_msg = (
#         "Leave request approved successfully"
#         if action =="Approved"
#         else "Leave request rejected successfully"
#     )

#     return jsonify({"message":success_msg}),200


# @app.route("/api/leave/decide", methods=["POST"])
# def decide_leave():
#     try:
#         data = request.get_json()

#         leave_id = data.get("leave_id")
#         action = data.get("action")
#         admin_id = data.get("admin_id")

#         if not leave_id or not action or not admin_id:
#             return jsonify({"error": "Missing required fields"}), 400

#         if action not in ["Approved", "Rejected"]:
#             return jsonify({"error": "Invalid action"}), 400

#         # Fetch leave request
#         leave = LeaveRequest.query.filter_by(id=leave_id).first()
#         if not leave:
#             return jsonify({"error": "Leave request not found"}), 404

#         # Fetch employee
#         employee = Employee.query.filter_by(emp_id=leave.emp_id).first()
#         if not employee:
#             return jsonify({"error": "Employee not found"}), 404

#         # APPROVE LEAVE
#         if action == "Approved":

#             # Calculate total leave days
#             total_days = (leave.end_date - leave.start_date).days + 1
#             leave.total_days = total_days

#             # Deduct from available leaves
#             if employee.remaining_leaves >= total_days:
#                 # Normal leave deduction
#                 employee.remaining_leaves -= total_days
#             else:
#                 # Not enough leaves → Extra leaves
#                 extra_taken = total_days - employee.remaining_leaves

#                 employee.extra_leaves += extra_taken
#                 employee.remaining_leaves = 0  # all used

#             # Update leave request fields
#             leave.status = "Approved"
#             leave.approved_by = admin_id
#             leave.approved_at = datetime.now()

#             db.session.commit()

#             return (
#                 jsonify(
#                     {
#                         "message": "Leave approved successfully",
#                         "total_days": total_days,
#                         "remaining_leaves": employee.remaining_leaves,
#                         "extra_leaves": employee.extra_leaves,
#                     }
#                 ),
#                 200,
#             )

#         # REJECT LEAVE
#         elif action == "Rejected":
#             leave.status = "Rejected"
#             leave.approved_by = admin_id
#             leave.approved_at = datetime.now()

#             db.session.commit()

#             return jsonify({"message": "Leave rejected successfully"}), 200

#     except Exception as e:
#         db.session.rollback()
#         return jsonify({"error": str(e)}), 500


@app.route("/api/leave/decide", methods=["POST"])
def decide_leave():
    data = request.get_json()

    leave_id = data.get("leave_id")
    action = data.get("action")
    admin_id = data.get("admin_id")

    if not leave_id or not action or not admin_id:
        return jsonify({"message": "Missing required fields"}), 400

    leave = LeaveRequest.query.get(leave_id)
    if not leave:
        return jsonify({"message": "Leave request not found"}), 404

    employee = Employee.query.filter_by(emp_id=leave.emp_id).first()
    balance = LeaveBalance.query.filter_by(emp_id=leave.emp_id).first()

    if not employee or not balance:
        return jsonify({"message": "Employee record missing"}), 404

    # Calculate number of leave days
    total_days = (leave.end_date - leave.start_date).days + 1

    if action == "Approved":
        leave.status = "Approved"
        leave.approved_by = admin_id
        leave.approved_at = datetime.utcnow()
        leave.total_days = total_days

        # Update employee table
        if employee.remaining_leaves >= total_days:
            employee.remaining_leaves -= total_days
        else:
            # Extra leave taken
            extra = total_days - employee.remaining_leaves
            employee.remaining_leaves = 0
            employee.used_leaves += extra

        # Update leave_balance table
        if balance.remaining_leaves >= total_days:
            balance.remaining_leaves -= total_days
            balance.used_leaves += total_days
        else:
            extra = total_days - balance.remaining_leaves
            balance.extra_leaves += extra
            balance.used_leaves += balance.remaining_leaves
            balance.remaining_leaves = 0

    elif action == "Rejected":
        leave.status = "Rejected"

    else:
        return jsonify({"message": "Invalid action"}), 400

    db.session.commit()
    return jsonify({"message": f"Leave {action.lower()} successfully"}), 200


# @app.route("/api/leave/balance/update",methods=["POST"])
# def update_leave_balance():
#     data = request.get_json()

#     emp_id = data.get("emp_id")
#     total_leaves = data.get("total_leaves")

#     if not emp_id or total_leaves is None:
#         return jsonify({"message":"Missing Required Fields"}),200

#     try:
#         total_leaves = int(total_leaves)
#         if total_leaves <= 0:
#             return jsonify({"message":"Total leaves must be non-negative"}),200
#     except:
#         return jsonify({"message":"Total leaves must be an integer"}),200

#     employee = Employee.query.filter_by(emp_id=emp_id).first()
#     if not employee:
#         return jsonify({"message":"Employee not found"}),200

#     employee.leave_balance = total_leaves
#     db.session.commit()

#     return jsonify({"message":"Leave balance updated sucessfully"}),200


# @app.route("/api/leave/balance/update", methods=["POST"])
# def update_leave_balance():
#     data = request.get_json()

#     emp_id = data.get("emp_id")
#     total = data.get("total_leaves")

#     if not emp_id or total is None:
#         return jsonify({"message": "Missing fields"}), 400

#     balance = LeaveBalance.query.filter_by(emp_id=emp_id).first()
#     if not balance:
#         return jsonify({"message": "Employee not found"}), 404

#     balance.total_leaves = total
#     balance.remaining_leaves = total  # Reset remaining
#     db.session.commit()

#     return jsonify({"message": "Leave balance updated successfully"}), 200


# @app.route("/api/leave/balance/update", methods=["POST"])
# def update_leave_balance():
#     data = request.get_json()
#     emp_id = data.get("emp_id")
#     total_leaves = data.get("total_leaves")

#     if not emp_id or total_leaves is None:
#         return jsonify({"message": "Missing fields"}), 400

#     employee = Employee.query.filter_by(emp_id=emp_id).first()

#     if not employee:
#         return jsonify({"message": "Employee not found"}), 404

#     employee.total_leaves = total_leaves
#     employee.remaining_leaves = total_leaves
#     db.session.commit()

#     return jsonify({"message": "Leave balance updated successfully"}), 200


# @app.route("/api/leave/balance/update", methods=["POST"])
# def update_leave_balance():
#     data = request.get_json()

#     emp_id = data.get("emp_id")
#     total_leaves = data.get("total_leaves")

#     if not emp_id or total_leaves is None:
#         return jsonify({"message": "Missing fields"}), 400

#     # Check if employee exists
#     employee = Employee.query.filter_by(emp_id=emp_id).first()
#     if not employee:
#         return jsonify({"message": "Employee not found"}), 404

#     # Check if leave balance entry exists
#     balance = LeaveBalance.query.filter_by(emp_id=emp_id).first()

#     if balance:
#         # Update
#         balance.total_leaves = total_leaves
#         balance.remaining_leaves = total_leaves
#     else:
#         # Insert new record
#         balance = LeaveBalance(
#             emp_id=emp_id,
#             total_leaves=total_leaves,
#             remaining_leaves=total_leaves,
#             extra_leaves=0,
#         )
#         db.session.add(balance)

#     db.session.commit()

#     return jsonify({"message": "Leave balance updated successfully"}), 200


@app.route("/api/leave/balance/update", methods=["POST"])
def update_leave_balance():
    data = request.get_json()

    emp_id = data.get("emp_id")
    total_leaves = data.get("total_leaves")

    if not emp_id or total_leaves is None:
        return jsonify({"message": "Missing required fields"}), 400

    # Find employee
    employee = Employee.query.filter_by(emp_id=emp_id).first()
    if not employee:
        return jsonify({"message": "Employee not found"}), 404

    # Update employee table
    employee.total_leaves = total_leaves
    employee.remaining_leaves = total_leaves

    # Update leave_balance table
    balance = LeaveBalance.query.filter_by(emp_id=emp_id).first()

    if not balance:
        balance = LeaveBalance(
            emp_id=emp_id,
            total_leaves=total_leaves,
            remaining_leaves=total_leaves,
            used_leaves=0,
            extra_leaves=0,
        )
        db.session.add(balance)
    else:
        balance.total_leaves = total_leaves
        balance.remaining_leaves = total_leaves
        balance.used_leaves = 0
        balance.extra_leaves = 0

    db.session.commit()
    return jsonify({"message": "Leave balance updated in both tables"}), 200


# Get statements according to the Api Documentation
@app.route("/api/employees", methods=["GET"])
def get_all_employees():
    try:
        employees = Employee.query.all()

        result = []
        for emp in employees:
            result.append(
                {
                    "id": emp.id,
                    "emp_id": emp.emp_id,
                    "name": emp.name,
                    "email": emp.email,
                    "phone": emp.phone,
                    "department": emp.department,
                    "designation": emp.designation,
                    "total_leaves": emp.total_leaves,
                    "remaining_leaves": emp.remaining_leaves,
                    # "used_leaves": emp.used_leaves,
                    "extra_leaves": emp.extra_leaves,
                    "created_at": emp.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                }
            )

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/employees/<int:id>", methods=["GET"])
def get_employee_by_id(id):
    try:
        # Find employee using DB primary key (id column)
        employee = Employee.query.get(id)

        if not employee:
            return jsonify({"message": "Employee not found"}), 404

        result = {
            "id": employee.id,
            "emp_id": employee.emp_id,
            "name": employee.name,
            "email": employee.email,
            "phone": employee.phone,
            "department": employee.department,
            "designation": employee.designation,
            "total_leaves": employee.total_leaves,
            "remaining_leaves": employee.remaining_leaves,
            # "used_leaves": employee.used_leaves,
            "extra_leaves": employee.extra_leaves,
            "created_at": employee.created_at.strftime("%Y-%m-%d %H:%M:%S"),
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/leave/requests", methods=["GET"])
def get_all_leave_requests():
    try:
        leaves = LeaveRequest.query.all()

        response = []

        for leave in leaves:

            employee = Employee.query.filter_by(emp_id=leave.emp_id).first()

            response.append(
                {
                    "id": leave.id,
                    "emp_id": leave.emp_id,
                    "name": employee.name,
                    # "start_date"
                    "department": employee.department,
                    "designation": employee.designation,
                    "start_date": str(leave.start_date),
                    "end_date": str(leave.end_date),
                    "reason": leave.reason,
                    "status": leave.status,
                    "total_days": leave.total_days,
                    "applied_at": leave.applied_at.strftime("%Y-%m-%d %H:%M:%S"),
                    "approved_at": (
                        leave.approved_at.strftime("%Y-%m-%d %H:%M:%S")
                        if leave.approved_at
                        else None
                    ),
                    "approved_by": leave.approved_by,
                    "created_at": leave.created_at.strftime("%Y-%m-%d %H:%M:%S"),
                    # "updated_at":leave.updated_at.strftime("%Y-%m-%d %H:%M:%S") if leave.updated_at else None,
                }
            )

        return jsonify({"leave_requests": response}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/leave/balance/<string:emp_id>", methods=["GET"])
def get_leave_balance(emp_id):
    try:
        leave_balance = LeaveBalance.query.filter_by(emp_id=emp_id).first()

        if not leave_balance:
            return jsonify({"message": "leave balance not found"}), 404

        result = {
            "emp_id": leave_balance.emp_id,
            "total_leaves": leave_balance.total_leaves,
            "used_leaves": leave_balance.used_leaves,
            "remaining_leaves": leave_balance.remaining_leaves,
            "extra_leaves": leave_balance.extra_leaves,
            "updated_at": leave_balance.updated_at.strftime("%Y-%m-%d %H-%M-%S"),
        }

        return jsonify(result), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/dashboard/attendance", methods=["GET"])
def attendance_dashboard():
    try:
        today = date.today()

        # Total Employees

        total_employees = Employee.query.count()

        # Employees that are present today
        present_today = Attendance.query.filter_by(in_date=today).count()

        # Employees that are absent today
        absent_today = total_employees - present_today

        # Employees on leave today
        on_leave = LeaveRequest.query.filter(
            LeaveRequest.start_date <= today,
            LeaveRequest.end_date >= today,
            LeaveRequest.status == "Approved",
        ).count()

        departments = []

        all_departments = db.session.query(Employee.department).distinct().all()

        for dept_tuple in all_departments:
            dept = dept_tuple[0]
            count = (
                db.session.query(Attendance)
                .join(Employee, Employee.id == Attendance.employee_id)
                .filter(Attendance.in_date == today, Employee.department == dept)
                .count()
            )

            departments.append({"department": dept, "present_today": count})

            # Weakly Attendance Data (last 7 days)

            weeklyData = []

            for i in range(7):
                day = today - timedelta(days=i)
                count = Attendance.query.filter_by(in_date=day).count()

                weeklyData.append({"Date": day.strftime("%Y-%mp-%d"), "Present": count})

            weeklyData.reverse()

            # Monthly Attendance Date (Last 30 days)

            monthly = []

            for m in range(1, 13):
                month_start = date(today.year, m, 1)
                month_end = date(today.year, m, calendar.monthrange(today.year, m)[1])

                month_present = Attendance.query.filter(
                    Attendance.in_date >= month_start, Attendance.in_date <= month_end
                ).count()

                total_working_days = calendar.monthrange(today.year, m)[1]

                # Attendance Rate = present/total employees *  working days

                total_possible = total_employees * total_working_days

                attendance_rate = (
                    (month_present / total_possible) * 100 if total_possible > 0 else 0
                )

                monthly.append(
                    {
                        "month": calendar.month_name[m],
                        "Attendance_Rate": round(attendance_rate, 2),
                    }
                )

                # late arrivals not implemented yetr

                late_arrivals = 0

                # Attendance rate for today
                attendanceRate = (
                    (present_today / total_employees * 100)
                    if total_employees > 0
                    else 0
                )

                # Final Response
                # return jsonify({
                #     "total_employees":total_employees,
                #     "present_today":present_today,
                #     "absent_today":absent_today,
                #     "on_leave":on_leave,
                #     "attendance_rate_today":round(attendanceRate,2),
                #     "departments":departments,
                #     "weekly_data":weeklyData,
                #     "monthly_data":monthly,
                #     "late_arrivals":late_arrivals
                # }),200

                return (
                    jsonify(
                        {
                            "absentToday": absent_today,
                            "attendanceRate": round(attendanceRate, 2),
                            "departments": departments,
                            "lateArrivals": late_arrivals,
                            "monthly": monthly,
                            "onLeave": on_leave,
                            "presentToday": present_today,
                            "totalEmployees": total_employees,
                            "weeklyData": weeklyData,
                        }
                    ),
                    200,
                )

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/attendance-report", methods=["GET"])
def attendance_report_by_date():
    try:
        req_date = request.args.get("date")

        if not req_date:
            return jsonify({"error": "Date query parameter is required"}), 400

        try:
            report_date = datetime.strptime(req_date, "%Y-%m-%d").date()
        except ValueError:
            return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

        records = (
            db.session.query(Attendance, Employee)
            .join(Employee, Employee.id == Attendance.employee_id)
            .filter(Attendance.in_date == report_date)
            .all()
        )

        result = []

        for attendance, employee in records:
            result.append(
                {
                    "department": employee.department,
                    "emp_id": employee.emp_id,
                    "employee_id": employee.id,
                    "name": employee.name,
                    "in_date": attendance.in_date.strftime("%Y-%m-%d"),
                    "in_time": (
                        attendance.in_time.strftime("%Y-%m-%d %H:%M:%S")
                        if attendance.in_time
                        else ""
                    ),
                    "out_time": (
                        attendance.out_time.strftime("%Y-%m-%d %H:%M:%S")
                        if attendance.out_time
                        else ""
                    ),
                    "designation": employee.designation,
                    "in_latitude": attendance.latitude if attendance.latitude else "",
                    "in_longitude": (
                        attendance.longitude if attendance.longitude else ""
                    ),
                }
            )

        return jsonify({"attendance_report": result}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route("/api/leave/on-leave-today", methods=["GET"])
def get_on_leave_today():
    try:
        today = date.today()

        # Fetch leave records where today is between start_date and end_date AND status = Approved
        leave_records = (
            db.session.query(LeaveRequest, Employee)
            .join(Employee, LeaveRequest.emp_id == Employee.emp_id)
            .filter(
                LeaveRequest.status == "Approved",
                LeaveRequest.start_date <= today,
                LeaveRequest.end_date >= today,
            )
            .all()
        )

        employees_list = []

        for leave, emp in leave_records:
            employees_list.append(
                {
                    "emp_id": emp.emp_id,
                    "name": emp.name,
                    "department": emp.department,
                    "designation": emp.designation,
                    "start_date": leave.start_date.strftime("%Y-%m-%d"),
                    "end_date": leave.end_date.strftime("%Y-%m-%d"),
                    "reason": leave.reason,
                }
            )

        return jsonify({"count": len(employees_list), "employees": employees_list}), 200

    except Exception as e:
        return jsonify({"error": str(e)}), 500


# @app.route("/api/employees/<int :emp_id>",methods=["PUT"])
# def update_employee(emp_id):
#     data = request.get_json()

#     name = data.get("name")
#     email = data.get("email")
#     phone = date.get("phone")
#     department = data.get("department")
#     designation = data.get("designation")
#     user_id = data.get("user_id")

#     if not all([name,email,phone,department,designation,user_id]):
#         return jsonify({"message":"Missing Required Fields"}),400

#     employee = Employee.query.filter_by(id=emp_id).first()

#     if not  employee:
#         return jsonify({"message":"Employee not found"}),404


#     employee.name = name
#     employee.email = email
#     employee.phone = phone
#     employee.department = department
#     employee.designation = designation
#     employee.updated_by = user_id
#     employee.updated_at = datetime.utcnow()

#     db.session.commit()

#     return jsonify({"message":"Employee details updated successfully"}),


# @app.route("/api/employees/<int:emp_id>", methods=["PUT"])
# def update_employee(emp_id):
#     data = request.get_json()

#     # Extract fields
#     name = data.get("name")
#     email = data.get("email")
#     phone = data.get("phone")
#     department = data.get("department")
#     designation = data.get("designation")
#     user_id = data.get("userId")  # Not used anywhere but required by documentation

#     # Validate required fields
#     if not all([name, email, phone, department, designation, user_id]):
#         return jsonify({"message": "Missing required fields"}), 400

#     # Find employee
#     employee = Employee.query.filter_by(id=emp_id).first()
#     if not employee:
#         return jsonify({"message": "Employee not found"}), 404

#     # Update employee fields
#     employee.name = name
#     employee.email = email
#     employee.phone = phone
#     employee.department = department
#     employee.designation = designation

#     db.session.commit()

#     return jsonify({"message": "Employee updated successfully"}), 200


@app.route("/api/employees/<int:emp_id>", methods=["PUT"])
def update_employee(emp_id):
    data = request.get_json()

    # Extract fields
    name = data.get("name")
    email = data.get("email")
    phone = data.get("phone")
    department = data.get("department")
    designation = data.get("designation")
    user_id = data.get("userId")  # Not used anywhere but required by documentation

    # Validate required fields
    if not all([name, email, phone, department, designation, user_id]):
        return jsonify({"message": "Missing required fields"}), 400

    # Find employee
    employee = Employee.query.filter_by(id=emp_id).first()
    if not employee:
        return jsonify({"message": "Employee not found"}), 404

    # Update employee fields
    employee.name = name
    employee.email = email
    employee.phone = phone
    employee.department = department
    employee.designation = designation

    db.session.commit()

    return jsonify({"message": "Employee updated successfully"}), 200


@app.route("/api/employees/<int:emp_id>", methods=["DELETE"])
def delete_employee(emp_id):

    employee = Employee.query.filter_by(id=emp_id).first()

    if not employee:
        return jsonify({"message": "Employee not found"}), 404

    db.session.delete(employee)
    db.session.commit()

    return jsonify({"message": "Employee deleted successfully"}), 200


# Active and Deactive feature
# @app.route("/api/employees/deactivate/<int:emp_id>", methods=["PUT"])
# def delete_soft_employee(emp_id):

#     employee = Employee.query.filter_by(id=emp_id).first()

#     if not employee:
#         return jsonify({"message": "Employee not found"}), 404

#     # Soft delete → mark inactive
#     # employee.is_active = False
#     employee.is_active = 0
#     db.session.commit()

#     return jsonify({"message": "Employee deactivated successfully"}), 200


# @app.route("/api/employees/activate/<int:emp_id>", methods=["PUT"])
# def activate_employee(emp_id):

#     employee = Employee.query.filter_by(id=emp_id).first()

#     if not employee:
#         return jsonify({"message": "Employee not found"}), 404

#     # employee.is_active = True
#     employee.is_active = 1
#     db.session.commit()

#     return jsonify({"message": "Employee activated successfully"}), 200


@app.route("/api/employees/deactivate/<int:emp_id>", methods=["PUT"])
def deactivate_employee(emp_id):
    employee = Employee.query.filter_by(id=emp_id).first()

    if not employee:
        return jsonify({"message": "Employee not found"}), 404

    employee.is_active = False
    db.session.commit()

    return jsonify({"message": "Employee deactivated successfully"}), 200


@app.route("/api/employees/activate/<int:emp_id>", methods=["PUT"])
def activate_employee(emp_id):

    employee = Employee.query.filter_by(id=emp_id).first()

    if not employee:
        return jsonify({"message": "Employee not found"}), 404

    # employee.is_active = True
    employee.is_active = 1
    db.session.commit()

    return jsonify({"message": "Employee activated successfully"}), 200


# Hard Delete of the employee Leave Request
@app.route("/api/leave/delete/<int:leave_id>",methods=["DELETE"])
def delete_leave_request(leave_id):
    
    leave = LeaveRequest.query.filter_by(id=leave_id).first()
    
    if not leave:
        return jsonify({"message":"Leave Request not found"}),404
    
    db.session.delete(leave)
    db.session.commit()
    
    return jsonify({"message":"Leave Request deleted successfully"}),200


# Soft Delete of the Employee Leave Request
@app.route("/api/leave/soft-delete/<int:leave_id>",methods=["PUT"])
def soft_delete_leave_request(leave_id):
    
    leave = LeaveRequest.query.filter_by(id = leave_id).first()
    
    if not leave:
        return jsonify({"message":"Leave Request not found"}),404
    
    leave.is_delted = True
    db.session.commit()
# print(app.url_map)


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    app.run(debug=True)
