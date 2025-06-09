import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any


class AppointmentManager:
    def __init__(self):
        self.appointments = {}
        self.next_id = 1

    def handle_rasa_intent(self, rasa_data: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Rasa-parsed appointment intent"""
        intent_name = rasa_data["intent"]["name"]
        entities = rasa_data["entities"]

        # Convert entities to slots
        slots = self._entities_to_slots(entities)

        # Debug: Print extracted entities and slots
        print(f"DEBUG - Intent: {intent_name}")
        print(f"DEBUG - Entities: {entities}")
        print(f"DEBUG - Slots: {slots}")

        if intent_name == "book_appointment":
            return self.create_appointment(slots)
        elif intent_name == "modify_appointment":
            return self.update_appointment(slots.get("appointment_id"), slots)
        elif intent_name == "cancel_appointment":
            return self.cancel_appointment(slots.get("appointment_id"))
        elif intent_name == "view_appointments":
            return self.get_appointments(slots)
        else:
            raise ValueError(f"Unsupported intent: {intent_name}")

    def _entities_to_slots(self, entities: List[Dict]) -> Dict[str, Any]:
        """Convert Rasa entities array to slots dictionary"""
        slots = {}

        for entity in entities:
            slots[entity["entity"]] = entity["value"]

            # Handle additional entity properties
            if "additional_info" in entity:
                slots[f"{entity['entity']}_info"] = entity["additional_info"]

        return slots

    def _normalize_doctor_name(self, name: str) -> str:
        """Normalize doctor name to ensure consistent format with Dr. prefix"""
        if not name:
            return ""
            
        # Remove any existing Dr. or Doctor prefix
        name = re.sub(r'^(dr\.?|doctor)\s+', '', str(name).strip(), flags=re.IGNORECASE)
        
        # Add Dr. prefix if not present
        if not name.lower().startswith('dr.'):
            name = f"Dr. {name}"
            
        return name

    def create_appointment(self, slots: Dict[str, Any]) -> Dict[str, Any]:
        """Create appointment from Rasa slots - now more flexible"""

        # Check if we have minimum required information
        if not slots.get("date") or not slots.get("time"):
            # Return info about missing slots for form handling
            missing_slots = []
            if not slots.get("date"):
                missing_slots.append("date")
            if not slots.get("time"):
                missing_slots.append("time")
            if not slots.get("doctor_name"):
                missing_slots.append("doctor_name")
            if not slots.get("reason"):
                missing_slots.append("reason")

            return {
                "success": False,
                "missing_slots": missing_slots,
                "message": f"I need more information. Please provide: {', '.join(missing_slots)}",
                "action": "activate_form"
            }

        appointment = {
            "id": self.next_id,
            "title": slots.get("reason") or slots.get("appointment_type") or "Medical Appointment",
            "date": self._normalize_date(slots["date"]),
            "time": self._normalize_time(slots["time"]),
            "duration": slots.get("duration", "30 minutes"),
            "doctor": self._normalize_doctor_name(slots.get("doctor_name") or slots.get("provider")),
            "patient": slots.get("patient_name"),
            "reason": slots.get("reason"),
            "location": slots.get("location") or slots.get("clinic"),
            "phone": slots.get("phone_number"),
            "status": "scheduled",
            "metadata": {
                "confidence": slots.get("confidence", 1.0),
                "rasa_session_id": slots.get("session_id"),
                "created_at": datetime.now().isoformat(),
                "updated_at": datetime.now().isoformat()
            }
        }

        # Update memory
        self.appointments[self.next_id] = appointment
        appointment_id = self.next_id
        self.next_id += 1

        return {
            "success": True,
            "appointment": appointment,
            "message": f"✅ Appointment booked!\n📅 Date: {appointment['date']}\n🕐 Time: {appointment['time']}\n👨‍⚕️ Doctor: {appointment['doctor']}\n📝 Reason: {appointment['reason'] or 'General'}",
            "db_string": self._serialize_for_database(appointment)
        }

    def create_appointment_from_slots(self, tracker_slots: Dict[str, Any]) -> Dict[str, Any]:
        """Create appointment using all slots from tracker (for form completion)"""
        # This method is called after form completion
        return self.create_appointment(tracker_slots)

    def update_appointment(self, appointment_id: Optional[str], slots: Dict[str, Any]) -> Dict[str, Any]:
        """Update existing appointment"""
        if not appointment_id:
            # Try to get the most recent appointment
            if self.appointments:
                appointment_id = max(self.appointments.keys())
            else:
                raise ValueError("No appointment ID provided and no appointments found")

        appt_id = int(appointment_id)
        appointment = self.appointments.get(appt_id)

        if not appointment:
            raise ValueError(f"Appointment with ID {appt_id} not found")

        # Update only provided slots
        updatable_fields = ["date", "time", "duration", "doctor", "reason", "location"]
        updates = {}

        for field in updatable_fields:
            if slots.get(field) is not None:
                if field == "date":
                    updates[field] = self._normalize_date(slots[field])
                elif field == "time":
                    updates[field] = self._normalize_time(slots[field])
                else:
                    updates[field] = slots[field]

        # Apply updates
        appointment.update(updates)
        appointment["metadata"]["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "appointment": appointment,
            "message": f"✅ Appointment {appt_id} updated!\n📅 {appointment['date']} at {appointment['time']}",
            "db_string": self._serialize_for_database(appointment)
        }

    def cancel_appointment(self, appointment_id: Optional[str]) -> Dict[str, Any]:
        """Cancel appointment"""
        if not appointment_id:
            # Try to get the most recent appointment
            if self.appointments:
                appointment_id = max(self.appointments.keys())
            else:
                raise ValueError("No appointment ID provided and no appointments found")

        appt_id = int(appointment_id)
        appointment = self.appointments.get(appt_id)

        if not appointment:
            raise ValueError(f"Appointment with ID {appt_id} not found")

        appointment["status"] = "cancelled"
        appointment["metadata"]["cancelled_at"] = datetime.now().isoformat()
        appointment["metadata"]["updated_at"] = datetime.now().isoformat()

        return {
            "success": True,
            "appointment": appointment,
            "message": f"❌ Appointment {appt_id} cancelled\n📅 Was: {appointment['date']} at {appointment['time']}",
            "db_string": self._serialize_for_database(appointment)
        }

    def get_appointments(self, slots: Dict[str, Any] = None) -> Dict[str, Any]:
        """Get appointments with optional filters"""
        if slots is None:
            slots = {}

        appointments = list(self.appointments.values())

        # Apply filters based on slots
        if slots.get("date"):
            filter_date = self._normalize_date(slots["date"])
            appointments = [apt for apt in appointments if apt["date"] == filter_date]

        if slots.get("doctor_name"):
            doctor_name = slots["doctor_name"].lower()
            appointments = [
                apt for apt in appointments
                if apt.get("doctor") and doctor_name in apt["doctor"].lower()
            ]

        if slots.get("status"):
            appointments = [apt for apt in appointments if apt["status"] == slots["status"]]

        return {
            "success": True,
            "appointments": appointments,
            "count": len(appointments),
            "message": f"Found {len(appointments)} appointment(s)"
        }

    def _serialize_for_database(self, appointment: Dict[str, Any]) -> str:
        """Serialize appointment for database storage"""
        db_data = {
            "id": appointment["id"],
            "title": appointment["title"],
            "datetime": f"{appointment['date']} {appointment['time']}",
            "duration": appointment["duration"],
            "doctor": appointment["doctor"],
            "patient": appointment["patient"],
            "reason": appointment["reason"],
            "location": appointment["location"],
            "phone": appointment["phone"],
            "status": appointment["status"],
            "metadata": appointment["metadata"]
        }

        return json.dumps(db_data)

    def _normalize_date(self, date_input: str) -> Optional[str]:
        """Normalize date from various formats to YYYY-MM-DD"""
        if not date_input:
            return None

        today = datetime.now().date()
        tomorrow = today + timedelta(days=1)

        date_lower = date_input.lower()

        if date_lower == "today":
            return today.isoformat()
        elif date_lower == "tomorrow":
            return tomorrow.isoformat()
        elif "next week" in date_lower:
            next_week = today + timedelta(weeks=1)
            return next_week.isoformat()
        elif "monday" in date_lower:
            # Find next Monday
            days_ahead = 0 - today.weekday()
            if days_ahead <= 0:  # Target day already happened this week
                days_ahead += 7
            next_monday = today + timedelta(days_ahead)
            return next_monday.isoformat()
        else:
            try:
                # Try to parse various date formats
                for fmt in ["%Y-%m-%d", "%m/%d/%Y", "%B %d", "%B %dth", "%B %dst", "%B %dnd", "%B %drd"]:
                    try:
                        parsed_date = datetime.strptime(date_input, fmt).date()
                        if parsed_date.year == 1900:  # No year provided, use current year
                            parsed_date = parsed_date.replace(year=today.year)
                        return parsed_date.isoformat()
                    except ValueError:
                        continue
                return date_input  # Return as-is if can't parse
            except:
                return date_input

    def _normalize_time(self, time_input: str) -> Optional[str]:
        """Normalize time input to 24-hour format (HH:MM)"""
        if not time_input:
            return None

        time_input = str(time_input).lower().strip()
        
        # Try common time formats
        time_patterns = [
            # 24-hour format
            r'^(\d{1,2}):(\d{2})$',  # 14:30
            r'^(\d{1,2})$',  # 14
            
            # 12-hour format
            r'^(\d{1,2})(?::(\d{2}))?\s*(am|pm)$',  # 2:30pm, 2pm
            r'^(\d{1,2})(?::(\d{2}))?\s*(a|p)$',  # 2:30p, 2p
            
            # Just numbers
            r'^(\d{1,2})$'  # 2, 14
        ]
        
        for pattern in time_patterns:
            match = re.match(pattern, time_input)
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                ampm = match.group(3) if len(match.groups()) > 2 else None
                
                # Convert to 24-hour format
                if ampm:
                    if ampm.startswith('p') and hour < 12:
                        hour += 12
                    elif ampm.startswith('a') and hour == 12:
                        hour = 0
                
                # Validate hour and minute
                if 0 <= hour <= 23 and 0 <= minute <= 59:
                    return f"{hour:02d}:{minute:02d}"
        
        return None 