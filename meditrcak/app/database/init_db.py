# app/database/init_db.py

from app.database.db import Base, engine
from app.auth.models import User  # import all models so Base.metadata can see them
from app.patients.models import Patient, GenderEnum, StatusEnum  # import patient model
from app.medications.models import Medication, PatientMedication, InactiveMedication, MedicationFormEnum, MedicationStatusEnum  # import medication models
from app.adherence.models import MedicationLog, AdherenceStats, AdherenceGoal  # import adherence models
from app.reminders.models import Reminder, ReminderSchedule  # import reminder models
from app.chat.models import ChatMessage  # import chat history model
from sqlalchemy.orm import Session
from app.database.db import get_db
from app.auth.utils import hash_password
from app.auth.models import RoleEnum
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime


def init_db():
    """Initialize the database by creating all tables."""
    print("📦 Initializing database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully.")
    
    # Create default admin user
    db: Session = next(get_db())
    try:
        # Check if admin exists
        admin_exists = db.query(User).filter(User.role == RoleEnum.admin).first()
        if not admin_exists:
            admin_user = User(
                full_name="Admin Doctor",
                email="johndoe@gmail.com",
                phone="+1234567890",
                password_hash=hash_password("xiSdbKciYAG9k2M"),
                role=RoleEnum.admin
            )
            db.add(admin_user)
            db.commit()
            print("✅ Default admin user created:")
            print("   Email: johndoe@gmail.com")
            print("   Password: xiSdbKciYAG9k2M")
    except Exception as e:
        print(f"⚠️  Error creating admin user: {e}")
        db.rollback()
    finally:
        db.close()


def populate_from_local_db():
    """Create sample data directly"""
    db: Session = next(get_db())

    try:
        print("🌱 Creating sample data...")

        user_id_map = {}
        patient_id_map = {}
        med_id_map = {}

        # Users data
        users_data = [
            {"id": 1, "full_name": "John Doe", "email": "johndoe@gmail.com", "phone": "+1-555-0123", "password_hash": "$2b$08$2Jo7ZPNY6k/hrzzKk5NAF.RHrt7RVnNZ1hK0Lc4oUhs41n2VEEgki", "role": "admin", "date_created": "2025-11-22 14:24:35"},
            {"id": 2, "full_name": "Sarah Johnson", "email": "sarah.johnson@gmail.com", "phone": "+212619169688", "password_hash": "$2b$08$gGPaMv6F/5DifTRMatW.7.kfNdo2OyKYhvqBbnrbMZ.pVLCdd4aCa", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 3, "full_name": "Michael Chen", "email": "michael.chen@gmail.com", "phone": "+1-555-1002", "password_hash": "$2b$08$GrLE/hkMNNT4ypVkcmJVOun4lF5dOVhLhJAtJOfc2oPa1yoekgYtK", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 4, "full_name": "Emily Rodriguez", "email": "emily.rodriguez@gmail.com", "phone": "+1-555-1003", "password_hash": "$2b$08$dAPxzPIg1JcTotSg.aHlKuXniEuqec1a2iVbQVoOMgs47OeFm6Rli", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 5, "full_name": "David Thompson", "email": "david.thompson@gmail.com", "phone": "+1-555-1004", "password_hash": "$2b$08$UHy1n1L6dTC/HXm05HO0iOaPO5fEkZV3CHAhhi52heSxzaOh16ary", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 6, "full_name": "Lisa Park", "email": "lisa.park@gmail.com", "phone": "+1-555-1005", "password_hash": "$2b$08$0een2d2XK2QITBwDNAHZrO7q6W939JecwjC/Ba2qumtmmkZi/.Jq", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 7, "full_name": "Robert Wilson", "email": "robert.wilson@gmail.com", "phone": "+1-555-1006", "password_hash": "$2b$08$VB6oKTLN3wZKAjcGw6VznuY5BQNknqYh1y6cFhg/J65HTyeiS866G", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 8, "full_name": "Maria Garcia", "email": "maria.garcia@gmail.com", "phone": "+1-555-1007", "password_hash": "$2b$08$dpaPe3VVlCXJj1VcUDJPOe7fX/ORZzUSIuMFaTh3YMDUQaMIUGA3K", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 9, "full_name": "James Brown", "email": "james.brown@gmail.com", "phone": "+1-555-1008", "password_hash": "$2b$08$oe.aMrBxvqwUTXC/UNcnrOtAr1lGws3g3WZ24ebJcKlS.0SgRml4y", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 10, "full_name": "Jennifer Lee", "email": "jennifer.lee@gmail.com", "phone": "+1-555-1009", "password_hash": "$2b$08$.XovMIWm3WvewuQ8oOxqGem0LqM6TQmaMQPpuRhXBasAFg6S/X7p6", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 11, "full_name": "Christopher Davis", "email": "christopher.davis@gmail.com", "phone": "+1-555-1010", "password_hash": "$2b$08$4E6BmNhu5wwT/ZXOWO6gW.7Ou5cq0l3Bwl jQJ5GmQ70O.CMv9Wy0S", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 12, "full_name": "ilham kholkhal", "email": "kholkhal3@gmail.com", "phone": "1 222222222", "password_hash": "$2b$08$OaRBoYazjX4wYWWio08ymOOy95qOeBqcosJI3cgwQPgi91QTE/Uxu", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 13, "full_name": "patient 12", "email": "patient12@gmail.com", "phone": "+212619169650", "password_hash": "$2b$08$rUeIHMHT2Gl.NAidAPS1y.gLUvwSCyQ60KesqOg/KCHcGG6elpoI6", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 14, "full_name": "John Doe", "email": "john.doe@example.com", "phone": "+1234567890", "password_hash": "$2b$08$f27ncQxUGYVGVRDAQXp2ROq7YYGyW2EVdlAlyvupEiM3AuRIsmL.y", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 15, "full_name": "Ilham El gharbi", "email": "ilham123@gmail.com", "phone": None, "password_hash": "$2b$08$INJbpJpTH0U8/pkr3JkIjOTFU5Kvi8u3g1ymgkiR4BD/pOS8s9Ptu", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 16, "full_name": "Hicham El gharbi", "email": "hicham123@gmail.com", "phone": "0699119024", "password_hash": "$2b$08$4x/CeN8o0rkl5UG07hkz7ea7inglGdNrWX.f5Z48PJ/.bJyfaEOqG", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 17, "full_name": "ilham gg", "email": "hicham1234@gmail.com", "phone": "0619169650", "password_hash": "$2b$08$/Y..Sg7wgz.8zakDnBuIWeEQuMjUmXTuOLZ5X8jM9cPKY9eII3bzi", "role": "patient", "date_created": "2025-11-22 14:24:35"},
            {"id": 18, "full_name": "ilho", "email": "kholkhal305@gmail.com", "phone": "0619169650", "password_hash": "$2b$08$Cag5uuS75x4d4p1WjjcY.eSeUb2ZIxpkhi.AWw4TQVuM5ueF0W0i", "role": "patient", "date_created": "2025-11-22 14:24:35"}
        ]

        # Create users
        print("👥 Creating users...")
        for u in users_data:
            existing = db.query(User).filter(User.email == u['email']).first()
            if existing:
                user_id_map[u['id']] = existing.id
                continue
            user = User(
                full_name=u['full_name'],
                email=u['email'],
                phone=u['phone'],
                password_hash=u['password_hash'],
                role=RoleEnum(u['role']),
                date_created=datetime.strptime(u['date_created'], '%Y-%m-%d %H:%M:%S') if u['date_created'] else None
            )
            db.add(user)
            db.flush()
            user_id_map[u['id']] = user.id
            print(f"✅ Created user: {user.email}")

        # Patients data
        patients_data = [
            {"id": 1, "user_id": 2, "date_of_birth": "2001-03-15", "gender": "female", "blood_type": "A+", "height": 165.0, "weight": 104.0, "status": "critical", "medical_history": "Hypertension diagnosed in 2025. Regular checkups.", "allergies": "Penicillin, Shellfish,ff", "current_medications": "Lisinopril 10mg daily, Aspirin 81mg daily", "assigned_admin_id": 1, "created_at": "2025-11-22 14:24:35", "updated_at": "2025-11-27 01:52:18"},
            {"id": 2, "user_id": 3, "date_of_birth": "1992-07-22", "gender": "male", "blood_type": "O-", "height": 178.0, "weight": 75.0, "status": "stable", "medical_history": "Asthma since childhood. Well controlled with medication.", "allergies": "None known", "current_medications": "Albuterol inhaler as needed, Fluticasone 100mcg daily", "assigned_admin_id": 1, "created_at": "2025-11-22 14:24:36", "updated_at": None},
            {"id": 3, "user_id": 4, "date_of_birth": "1978-11-08", "gender": "female", "blood_type": "B+", "height": 162.0, "weight": 58.0, "status": "under_observation", "medical_history": "Type 2 Diabetes diagnosed in 2019. Managing with diet and medication.", "allergies": "Sulfa drugs", "current_medications": "Metformin 500mg twice daily, Vitamin D3 2000 IU daily", "assigned_admin_id": 1, "created_at": "2025-11-22 14:24:36", "updated_at": None},
            {"id": 4, "user_id": 5, "date_of_birth": "1965-05-30", "gender": "male", "blood_type": "AB+", "height": 175.0, "weight": 82.0, "status": "critical", "medical_history": "Heart disease. Recent bypass surgery in 2024.", "allergies": "Iodine contrast, Latex", "current_medications": "Warfarin 5mg daily, Atorvastatin 40mg daily, Clopidogrel 75mg daily, Lisinopril 20mg daily", "assigned_admin_id": 1, "created_at": "2025-11-22 14:24:36", "updated_at": None},
            {"id": 5, "user_id": 6, "date_of_birth": "1990-01-12", "gender": "female", "blood_type": "A-", "height": 168.0, "weight": 62.0, "status": "stable", "medical_history": "Migraine headaches. Occasional episodes.", "allergies": "Codeine, NSAIDs", "current_medications": "Topiramate 50mg daily, Sumatriptan as needed", "assigned_admin_id": 1, "created_at": "2025-11-22 14:24:37", "updated_at": None},
            {"id": 6, "user_id": 7, "date_of_birth": "1982-09-18", "gender": "male", "blood_type": "O+", "height": 183.0, "weight": 88.0, "status": "stable", "medical_history": "High cholesterol. Family history of heart disease.", "allergies": "None", "current_medications": "Rosuvastatin 20mg daily, Omega-3 fish oil 1000mg daily", "assigned_admin_id": 1, "created_at": "2025-11-22 14:24:37", "updated_at": None},
            {"id": 7, "user_id": 8, "date_of_birth": "1975-12-03", "gender": "female", "blood_type": "B-", "height": 158.0, "weight": 55.0, "status": "under_observation", "medical_history": "Thyroid issues. Hypothyroidism diagnosed in 2018.", "allergies": "Amoxicillin", "current_medications": "Levothyroxine 75mcg daily, Calcium 500mg + Vitamin D 400 IU daily", "assigned_admin_id": 1, "created_at": "2025-11-22 14:24:37", "updated_at": None},
            {"id": 8, "user_id": 9, "date_of_birth": "1995-04-25", "gender": "male", "blood_type": "A+", "height": 172.0, "weight": 70.0, "status": "stable", "medical_history": "Seasonal allergies. No major health issues.", "allergies": "Pollen, Dust mites", "current_medications": "Loratadine 10mg daily (seasonal), Multivitamin daily", "assigned_admin_id": 1, "created_at": "2025-11-22 14:24:38", "updated_at": None},
            {"id": 9, "user_id": 10, "date_of_birth": "1988-06-14", "gender": "female", "blood_type": "O+", "height": 170.0, "weight": 68.0, "status": "stable", "medical_history": "Pregnancy in 2023. Delivered healthy baby. Postpartum checkup normal.", "allergies": "None", "current_medications": "Prenatal vitamins, Iron supplement 65mg daily", "assigned_admin_id": 1, "created_at": "2025-11-22 14:24:38", "updated_at": None},
            {"id": 10, "user_id": 11, "date_of_birth": "1970-08-09", "gender": "male", "blood_type": "AB-", "height": 180.0, "weight": 85.0, "status": "critical", "medical_history": "Chronic kidney disease. On dialysis 3x weekly. Kidney transplant candidate.", "allergies": "Morphine, Contrast dye", "current_medications": "Epoetin alfa 4000 units 3x weekly, Phosphate binders, Vitamin D analogs, Blood pressure medications", "assigned_admin_id": 1, "created_at": "2025-11-22 14:24:38", "updated_at": None},
            {"id": 11, "user_id": 12, "date_of_birth": None, "gender": None, "blood_type": None, "height": None, "weight": None, "status": "stable", "medical_history": None, "allergies": None, "current_medications": None, "assigned_admin_id": 1, "created_at": "2025-11-22 15:03:15", "updated_at": None},
            {"id": 12, "user_id": 13, "date_of_birth": None, "gender": None, "blood_type": None, "height": None, "weight": None, "status": "stable", "medical_history": None, "allergies": None, "current_medications": None, "assigned_admin_id": 1, "created_at": "2025-11-22 19:52:42", "updated_at": None},
            {"id": 13, "user_id": 14, "date_of_birth": None, "gender": None, "blood_type": None, "height": None, "weight": None, "status": "stable", "medical_history": None, "allergies": None, "current_medications": None, "assigned_admin_id": 1, "created_at": "2025-11-22 20:31:52", "updated_at": None},
            {"id": 14, "user_id": 15, "date_of_birth": None, "gender": None, "blood_type": None, "height": None, "weight": None, "status": "stable", "medical_history": None, "allergies": None, "current_medications": None, "assigned_admin_id": 1, "created_at": "2025-11-23 16:33:14", "updated_at": None},
            {"id": 15, "user_id": 16, "date_of_birth": None, "gender": None, "blood_type": None, "height": None, "weight": None, "status": "stable", "medical_history": None, "allergies": None, "current_medications": None, "assigned_admin_id": 1, "created_at": "2025-11-23 16:43:25", "updated_at": None},
            {"id": 16, "user_id": 17, "date_of_birth": None, "gender": None, "blood_type": None, "height": None, "weight": None, "status": "stable", "medical_history": None, "allergies": None, "current_medications": None, "assigned_admin_id": 1, "created_at": "2025-11-23 18:25:01", "updated_at": None},
            {"id": 17, "user_id": 18, "date_of_birth": None, "gender": None, "blood_type": None, "height": None, "weight": None, "status": "stable", "medical_history": None, "allergies": None, "current_medications": None, "assigned_admin_id": 1, "created_at": "2025-11-25 19:33:45", "updated_at": None}
        ]

        # Create patients
        print("🏥 Creating patients...")
        for p in patients_data:
            patient = Patient(
                user_id=user_id_map[p['user_id']],
                date_of_birth=datetime.strptime(p['date_of_birth'], '%Y-%m-%d').date() if p['date_of_birth'] else None,
                gender=GenderEnum(p['gender']) if p['gender'] else None,
                blood_type=p['blood_type'],
                height=p['height'],
                weight=p['weight'],
                status=StatusEnum(p['status']),
                medical_history=p['medical_history'],
                allergies=p['allergies'],
                current_medications=p['current_medications'],
                assigned_admin_id=user_id_map[p['assigned_admin_id']] if p['assigned_admin_id'] else None,
                created_at=datetime.strptime(p['created_at'], '%Y-%m-%d %H:%M:%S') if p['created_at'] else None,
                updated_at=datetime.strptime(p['updated_at'], '%Y-%m-%d %H:%M:%S') if p['updated_at'] else None
            )
            db.add(patient)
            db.flush()
            patient_id_map[p['id']] = patient.id
            print(f"✅ Created patient for user ID: {patient.user_id}")

        # Medications data
        medications_data = [
            {"id": 1, "name": "Lisinopril", "form": "tablet", "dosage": "100mg", "side_effects": "Dizziness, dry cough, ,headache", "interactions": "Monitor blood pressure regularly. Avoid potassium supplements.", "created_by": 1, "created_at": "2025-11-23 10:52:14", "updated_at": "2025-11-27 02:11:11"},
            {"id": 2, "name": "Metformin", "form": "tablet", "dosage": "500mg", "side_effects": "Nausea, diarrhea, stomach upset", "interactions": "Take with food. Monitor kidney function.", "created_by": 1, "created_at": "2025-11-23 10:52:14", "updated_at": None},
            {"id": 3, "name": "Atorvastatin", "form": "tablet", "dosage": "20mg", "side_effects": "Muscle pain, headache, nausea", "interactions": "Avoid grapefruit juice. Take at bedtime.", "created_by": 1, "created_at": "2025-11-23 10:52:14", "updated_at": None},
            {"id": 4, "name": "Amlodipine", "form": "tablet", "dosage": "5mg", "side_effects": "Swelling of ankles, dizziness, flushing", "interactions": "May cause drowsiness. Rise slowly from sitting position.", "created_by": 1, "created_at": "2025-11-23 10:52:14", "updated_at": None},
            {"id": 5, "name": "Levothyroxine", "form": "tablet", "dosage": "100mcg", "side_effects": "Weight changes, anxiety, tremors", "interactions": "Take on empty stomach, 30 minutes before breakfast.", "created_by": 1, "created_at": "2025-11-23 10:52:14", "updated_at": None},
            {"id": 6, "name": "Omeprazole", "form": "capsule", "dosage": "20mg", "side_effects": "Headache, nausea, diarrhea", "interactions": "Take before meals. Long-term use may affect vitamin B12 absorption.", "created_by": 1, "created_at": "2025-11-23 10:52:14", "updated_at": None},
            {"id": 7, "name": "Sertraline", "form": "tablet", "dosage": "50mg", "side_effects": "Nausea, drowsiness, dry mouth", "interactions": "May take 2-4 weeks for full effect. Do not stop abruptly.", "created_by": 1, "created_at": "2025-11-23 10:52:14", "updated_at": None},
            {"id": 8, "name": "Gabapentin", "form": "capsule", "dosage": "300mg", "side_effects": "Drowsiness, dizziness, fatigue", "interactions": "May cause drowsiness. Do not drive until you know how it affects you.", "created_by": 1, "created_at": "2025-11-23 10:52:15", "updated_at": None},
            {"id": 9, "name": "Losartan", "form": "tablet", "dosage": "50mg", "side_effects": "Dizziness, fatigue, cold-like symptoms", "interactions": "Monitor blood pressure. Avoid potassium supplements.", "created_by": 1, "created_at": "2025-11-23 10:52:15", "updated_at": None},
            {"id": 10, "name": "Pantoprazole", "form": "tablet", "dosage": "40mg", "side_effects": "Headache, nausea, stomach pain", "interactions": "Take 30 minutes before a meal.", "created_by": 1, "created_at": "2025-11-23 10:52:15", "updated_at": None},
            {"id": 11, "name": "Albuterol", "form": "inhaler", "dosage": "900mcg", "side_effects": "Nervousness, shakiness, rapid heartbeat", "interactions": "Use as needed for breathing problems. Rinse mouth after use.", "created_by": 1, "created_at": "2025-11-23 10:52:15", "updated_at": "2025-11-26 21:17:26"},
            {"id": 12, "name": "Aspirin", "form": "tablet", "dosage": "81mg", "side_effects": "Stomach upset, heartburn", "interactions": "Take with food. May increase bleeding risk.", "created_by": 1, "created_at": "2025-11-23 10:52:15", "updated_at": None},
            {"id": 14, "name": "monsif", "form": "inhaler", "dosage": "xwk1bo", "side_effects": " xkb kqbb", "interactions": " x", "created_by": 1, "created_at": "2025-11-27 13:05:32", "updated_at": "2025-11-27 13:08:54"},
            {"id": 15, "name": "hi", "form": "drops", "dosage": "266k", "side_effects": "x w1k", "interactions": "svuwfxi", "created_by": 1, "created_at": "2025-11-28 15:39:22", "updated_at": None}
        ]

        # Create medications
        print("💊 Creating medications...")
        for m in medications_data:
            med = Medication(
                name=m['name'],
                form=MedicationFormEnum(m['form']),
                default_dosage=m['dosage'],
                side_effects=m['side_effects'],
                warnings=m['interactions'],
                created_by=user_id_map[m['created_by']],
                created_at=datetime.strptime(m['created_at'], '%Y-%m-%d %H:%M:%S') if m['created_at'] else None,
                updated_at=datetime.strptime(m['updated_at'], '%Y-%m-%d %H:%M:%S') if m['updated_at'] else None
            )
            db.add(med)
            db.flush()
            med_id_map[m['id']] = med.id
            print(f"✅ Created medication: {med.name}")

        # Patient medications data
        patient_medications_data = [
            {"id": 1, "patient_id": 1, "medication_id": 1, "prescribed_by": 1, "dosage_instructions": "100mg", "times_per_day": 2, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Take once daily in the morning", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": "2025-11-27 01:39:41"},
            {"id": 2, "patient_id": 1, "medication_id": 2, "prescribed_by": 1, "dosage_instructions": "500mg", "times_per_day": 4, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Take with breakfast and dinner", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": "2025-11-27 01:49:15"},
            {"id": 3, "patient_id": 1, "medication_id": 12, "prescribed_by": 1, "dosage_instructions": "81mg", "times_per_day": 1, "start_date": "2025-11-09", "end_date": None, "status": "stopped", "notes": "Take once daily with food", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": "2025-11-27 01:59:08"},
            {"id": 4, "patient_id": 2, "medication_id": 3, "prescribed_by": 1, "dosage_instructions": "20mg", "times_per_day": 1, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Take once daily at bedtime", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": None},
            {"id": 5, "patient_id": 2, "medication_id": 6, "prescribed_by": 1, "dosage_instructions": "20mg", "times_per_day": 1, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Take once daily before breakfast", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": None},
            {"id": 6, "patient_id": 3, "medication_id": 5, "prescribed_by": 1, "dosage_instructions": "100mcg", "times_per_day": 1, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Take once daily on empty stomach, 30 minutes before breakfast", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": None},
            {"id": 7, "patient_id": 4, "medication_id": 4, "prescribed_by": 1, "dosage_instructions": "5mg", "times_per_day": 1, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Take once daily in the morning", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": None},
            {"id": 8, "patient_id": 4, "medication_id": 9, "prescribed_by": 1, "dosage_instructions": "50mg", "times_per_day": 1, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Take once daily with or without food", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": None},
            {"id": 9, "patient_id": 5, "medication_id": 7, "prescribed_by": 1, "dosage_instructions": "50mg", "times_per_day": 1, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Take once daily in the morning", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": None},
            {"id": 10, "patient_id": 5, "medication_id": 8, "prescribed_by": 1, "dosage_instructions": "300mg", "times_per_day": 3, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Take three times daily", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": None},
            {"id": 11, "patient_id": 6, "medication_id": 10, "prescribed_by": 1, "dosage_instructions": "40mg", "times_per_day": 1, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Take once daily, 30 minutes before breakfast", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": None},
            {"id": 12, "patient_id": 7, "medication_id": 11, "prescribed_by": 1, "dosage_instructions": "2 puffs", "times_per_day": 4, "start_date": "2025-11-09", "end_date": None, "status": "active", "notes": "Use as needed for breathing problems, up to 4 times daily", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-23 10:52:59", "updated_at": None},
            {"id": 17, "patient_id": 2, "medication_id": 2, "prescribed_by": 1, "dosage_instructions": "500mg", "times_per_day": 1, "start_date": "2025-11-27", "end_date": None, "status": "active", "notes": "before food", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-27 12:47:48", "updated_at": "2025-11-27 12:53:56"},
            {"id": 18, "patient_id": 2, "medication_id": 12, "prescribed_by": 1, "dosage_instructions": "81mg", "times_per_day": 1, "start_date": "2025-11-27", "end_date": None, "status": "stopped", "notes": "take before morfine", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-27 12:59:34", "updated_at": "2025-11-27 14:07:18"},
            {"id": 20, "patient_id": 2, "medication_id": 9, "prescribed_by": 1, "dosage_instructions": "50mg", "times_per_day": 1, "start_date": "2025-11-27", "end_date": None, "status": "active", "notes": "", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-27 13:03:33", "updated_at": "2025-11-27 13:48:12"},
            {"id": 21, "patient_id": 2, "medication_id": 7, "prescribed_by": 1, "dosage_instructions": "50mg", "times_per_day": 1, "start_date": "2025-11-27", "end_date": None, "status": "active", "notes": "vhkihvo", "confirmed_by_patient": 1, "created_by": 1, "created_at": "2025-11-27 14:04:33", "updated_at": "2025-11-27 14:04:48"},
            {"id": 22, "patient_id": 2, "medication_id": 14, "prescribed_by": 1, "dosage_instructions": "xwk1bo", "times_per_day": 1, "start_date": "2025-11-27", "end_date": None, "status": "pending", "notes": " n j", "confirmed_by_patient": 0, "created_by": 1, "created_at": "2025-11-27 14:09:29", "updated_at": None}
        ]

        # Create patient medications
        print("💉 Creating patient medications...")
        for pm in patient_medications_data:
            pmed = PatientMedication(
                patient_id=patient_id_map[pm['patient_id']],
                medication_id=med_id_map[pm['medication_id']],
                dosage=pm['dosage_instructions'],
                instructions=pm['notes'],
                times_per_day=pm['times_per_day'],
                start_date=datetime.strptime(pm['start_date'], '%Y-%m-%d').date() if pm['start_date'] else None,
                end_date=datetime.strptime(pm['end_date'], '%Y-%m-%d').date() if pm['end_date'] else None,
                status=MedicationStatusEnum(pm['status']),
                confirmed_by_patient=bool(pm['confirmed_by_patient']),
                assigned_by_doctor=user_id_map[pm['prescribed_by']],
                created_at=datetime.strptime(pm['created_at'], '%Y-%m-%d %H:%M:%S') if pm['created_at'] else None,
                updated_at=datetime.strptime(pm['updated_at'], '%Y-%m-%d %H:%M:%S') if pm['updated_at'] else None
            )
            db.add(pmed)
            db.flush()
            print(f"✅ Created patient medication: {pmed.id}")

        db.commit()
        print("🎉 Population completed!")
        return "Population successful"

    except Exception as e:
        print(f"❌ Error during population: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return f"Failed: {e}"
    finally:
        db.close()

