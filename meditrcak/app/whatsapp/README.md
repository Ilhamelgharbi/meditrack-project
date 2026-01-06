# WhatsApp Integration for MediTrack AI

This package handles WhatsApp messaging for medication reminders and responses using Twilio's Content API (Templates).

## 🚨 Important: Templates Required for Reminders

WhatsApp **does NOT allow free text** for proactive messages like medication reminders. You **MUST use templates** for:

- ✅ Medication reminders
- ✅ Alerts
- ✅ Notifications
- ✅ Proactive messages

Use **free text** for:
- ✅ Agent replies
- ✅ Conversations
- ✅ Confirmations

## 📋 Setup

### 1. Twilio Configuration

Your `.env` file should have:
```env
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxxxx
TWILIO_WHATSAPP_NUMBER=whatsapp:+14155238886
```

### 2. WhatsApp Templates

Create templates in your Twilio Console:

**Template Name:** `medication_reminder`
**Content:**
```
💊 Medication Reminder

It's time to take your {{1}} on {{2}}.

Reply YES once taken.
```

**Approved Variables:**
- `{{1}}` = Date (e.g., "12/20")
- `{{2}}` = Time (e.g., "3pm")

## 📤 Sending Reminders

### Basic Usage

```python
from app.whatsapp import send_medication_reminder

result = send_medication_reminder(
    to_phone="+212619169650",
    medication_name="Aspirin",
    date="12/20",
    time="3pm",
    dosage="100mg"
)

if result["success"]:
    print(f"Reminder sent! SID: {result['message_sid']}")
else:
    print(f"Failed: {result['error']}")
```

### Convenience Functions

```python
from app.whatsapp import send_morning_reminder, send_evening_reminder

# Morning reminder
send_morning_reminder("+212619169650", "Vitamin D", "2000 IU")

# Evening reminder
send_evening_reminder("+212619169650", "Blood Pressure Med", "10mg")
```

### Custom Templates

```python
from app.whatsapp import send_custom_reminder_template

result = send_custom_reminder_template(
    to_phone="+212619169650",
    template_sid="HXyour-template-sid",
    variables={"1": "12/20", "2": "3pm", "3": "Aspirin"}
)
```

## 📥 Handling Responses

When users reply to templates (YES, TAKEN, SKIP, etc.), responses come through your webhook.

### Automatic Processing

The system automatically detects reminder responses and logs medication actions:

- ✅ **YES, TAKEN, DONE** → Logs as "taken"
- ✅ **SKIP, LATER** → Logs as "skipped"
- ✅ **NO, MISSED** → Logs as "missed"

### Manual Processing

```python
from app.whatsapp import handle_whatsapp_template_response

result = handle_whatsapp_template_response(
    user_phone="whatsapp:+212619169650",
    message_body="YES",
    db=session
)

if result["success"]:
    print(f"Action logged: {result['action']}")
```

## 🔄 Integration with Reminder System

The `process_reminders.py` script automatically uses template-based sending:

```bash
# Test reminders (dry run)
python process_reminders.py --dry-run

# Send actual reminders
python process_reminders.py
```

## 🏗 Architecture

```
Scheduler/Process
    ↓
send_medication_reminder()   ← Template Message
    ↓
WhatsApp User
    ↓
POST /assistant/whatsapp     ← Webhook
    ↓
TemplateResponseHandler      ← Detect & Log Action
    ↓
MedicationLog + AdherenceStats
```

## 🧪 Testing

### Test Reminder Sending

```python
from app.whatsapp.reminder_sender import test_reminder
test_reminder()
```

### Test Response Handling

```python
from app.whatsapp.template_response_handler import TemplateResponseHandler

handler = TemplateResponseHandler(db)
result = handler.handle_reminder_response("whatsapp:+212619169650", "YES")
```

## 📊 Template Response Keywords

The system recognizes these responses:

**Positive (Taken):**
- YES, TAKEN, DONE, TOOK IT, CONFIRMED, ✓, ✅

**Skip/Delay:**
- SKIP, LATER, SNOOZE, REMIND LATER

**Negative (Missed):**
- NO, MISSED, FORGOT, CAN'T, WON'T

## 🚨 Production Notes

1. **Templates must be approved** by WhatsApp before use in production
2. **Sandbox works** with free text, but production requires templates
3. **Rate limits** apply to template messages
4. **Opt-in required** - users must initiate conversation first

## 🔧 Configuration

Update these values in your Twilio Console:

- `REMINDER_TEMPLATE_SID` - Your approved medication reminder template
- `TWILIO_WHATSAPP_NUMBER` - Your WhatsApp-enabled Twilio number

## 📈 Monitoring

Check logs for:
- Successful reminder sends
- Response processing
- Failed deliveries
- Template approval status