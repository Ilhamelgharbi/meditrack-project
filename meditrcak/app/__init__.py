# Import all models to register them with SQLAlchemy
from app.auth.models import User
from app.patients.models import Patient
from app.medications.models import Medication, PatientMedication, InactiveMedication
from app.reminders.models import Reminder, ReminderSchedule, WhatsAppMessage, NotificationPreference
from app.adherence.models import MedicationLog, AdherenceStats, AdherenceGoal