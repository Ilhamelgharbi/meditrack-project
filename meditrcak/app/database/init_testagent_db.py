from sqlalchemy.orm import Session
from app.database.db import Base, engine
from app.config.settings import settings
from app.auth.models import User
from app.patients.models import Patient, GenderEnum, StatusEnum
from app.medications.models import Medication, PatientMedication, InactiveMedication, MedicationFormEnum, MedicationStatusEnum
from app.database.db import get_db
from app.auth.utils import hash_password
from app.auth.models import RoleEnum
import os
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import json
from datetime import datetime


def init_testagent_db():
    """Initialize the testagent database with only John Doe and Ilham Elgharbi as patients"""
    print("📦 Initializing testagent database...")
    Base.metadata.create_all(bind=engine)
    print("✅ Testagent database initialized successfully.")

    # Note: Users will be created in populate_testagent_db()


def populate_testagent_db():
    """Create sample data for testagent database with only John Doe and Ilham Elgharbi"""
    db: Session = next(get_db())

    try:
        print("🌱 Creating testagent sample data...")

        user_id_map = {}
        patient_id_map = {}
        med_id_map = {}

        # Only include John Doe as admin and Ilham Elgharbi as patient
        users_data = [
            {"id": 1, "full_name": "John Doe", "email": "johndoe@gmail.com", "phone": "+1234567890", "password_hash": "$2b$08$2Jo7ZPNY6k/hrzzKk5NAF.RHrt7RVnNZ1hK0Lc4oUhs41n2VEEgki", "role": "admin", "date_created": "2025-11-22 14:24:35"},
            {"id": 2, "full_name": "Ilham El gharbi", "email": "ilham123@gmail.com", "phone": None, "password_hash": "$2b$08$INJbpJpTH0U8/pkr3JkIjOTFU5Kvi8u3g1ymgkiR4BD/pOS8s9Ptu", "role": "patient", "date_created": "2025-11-22 14:24:35"}
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

        # Only include patient for Ilham Elgharbi

        # Only include patient for Ilham Elgharbi
        patients_data = [
            {"id": 1, "user_id": 2, "date_of_birth": None, "gender": None, "blood_type": None, "height": None, "weight": None, "status": "stable", "medical_history": None, "allergies": None, "current_medications": None, "assigned_admin_id": 1, "created_at": "2025-11-23 16:33:14", "updated_at": None}
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

        # Include all medications (they're shared)
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
            {"id": 12, "name": "Aspirin", "form": "tablet", "dosage": "81mg", "side_effects": "Stomach upset, heartburn", "interactions": "Take with food. May increase bleeding risk.", "created_by": 1, "created_at": "2025-11-23 10:52:15", "updated_at": None}
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

        # No patient medications assigned yet - just the catalog
        patient_medications_data = []

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
        print("🎉 Testagent population completed!")
        print("\n📋 Test Users:")
        print("Admin: johndoe@gmail.com / xiSdbKciYAG9k2M (John Doe)")
        print("Patient: ilham123@gmail.com (Ilham Elgharbi - ID: 2, no medications assigned yet)")
        print("💊 Medication catalog available for assignment")
        return "Population successful"

    except Exception as e:
        print(f"❌ Error during population: {e}")
        import traceback
        traceback.print_exc()
        db.rollback()
        return f"Failed: {e}"
    finally:
        db.close()