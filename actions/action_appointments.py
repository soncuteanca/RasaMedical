from typing import Any, Dict, List, Text
import re

from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, FollowupAction
from rasa_sdk.types import DomainDict
from .appointment_manager import AppointmentManager

appointment_mgr = AppointmentManager()


class ActionBookAppointment(Action):
    def name(self):
        return "action_book_appointment"

    async def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        try:
            entities = tracker.latest_message.get("entities", [])
            intent = tracker.latest_message.get("intent", {})
            text = tracker.latest_message.get("text")

            response = appointment_mgr.handle_rasa_intent({
                "intent": intent,
                "entities": entities,
                "text": text
            })

            if response.get("success"):
                dispatcher.utter_message(text=response["message"])
                return [SlotSet("appointment_id", response["appointment"]["id"])]
            else:
                # Missing required info - activate form
                dispatcher.utter_message(text=response["message"])
                return [FollowupAction("appointment_form")]

        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn't book your appointment: {str(e)}")
            return []


class ValidateAppointmentForm(FormValidationAction):
    def name(self) -> str:
        return "validate_appointment_form"

    def validate_date(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[str, Any]:
        """Validate date slot."""
        if slot_value:
            normalized_date = appointment_mgr._normalize_date(slot_value)
            if normalized_date:
                return {"date": normalized_date}
        
        dispatcher.utter_message(text="Please provide a valid date (e.g., tomorrow, June 15th, next Monday)")
        return {"date": None}

    def validate_time(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[str, Any]:
        """Validate time slot."""
        if not slot_value:
            dispatcher.utter_message(text="Please provide a valid time like '2 PM' or '14:00'")
            return {"time": None}

        # Try to normalize the time
        normalized_time = appointment_mgr._normalize_time(str(slot_value))
        if normalized_time:
            return {"time": normalized_time}
        
        # Additional time format handling
        time_patterns = [
            r'(\d{1,2})(?::(\d{2}))?\s*(am|pm)?',  # 2, 2:30, 2pm, 2:30pm
            r'(\d{1,2})',  # Just a number
            r'(\d{1,2})(?::(\d{2}))'  # 14:30
        ]
        
        for pattern in time_patterns:
            match = re.match(pattern, str(slot_value).lower())
            if match:
                hour = int(match.group(1))
                minute = int(match.group(2)) if match.group(2) else 0
                ampm = match.group(3) if match.group(3) else None
                
                # Convert to 24-hour format
                if ampm:
                    if ampm.startswith('p') and hour < 12:
                        hour += 12
                    elif ampm.startswith('a') and hour == 12:
                        hour = 0
                
                # Format time
                formatted_time = f"{hour:02d}:{minute:02d}"
                return {"time": formatted_time}
        
        dispatcher.utter_message(text="Please provide a valid time like '2 PM' or '14:00'")
        return {"time": None}

    def validate_doctor_name(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[str, Any]:
        """Validate doctor name slot."""
        if slot_value:
            # Remove any "Dr." or "Doctor" prefix and normalize
            doctor_name = str(slot_value).lower()
            doctor_name = re.sub(r'^(dr\.?|doctor)\s+', '', doctor_name)
            return {"doctor_name": doctor_name.title()}
        
        dispatcher.utter_message(text="Please specify which doctor you would like to see")
        return {"doctor_name": None}

    def validate_reason(
            self,
            slot_value: Any,
            dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: DomainDict,
    ) -> Dict[str, Any]:
        """Validate reason slot."""
        if not slot_value:
            dispatcher.utter_message(text="Can you briefly describe the reason for your visit?")
            return {"reason": None}

        # Accept any non-empty reason that's at least 2 characters
        reason = str(slot_value).strip()
        if len(reason) >= 2:
            return {"reason": reason}
        
        dispatcher.utter_message(text="Can you briefly describe the reason for your visit?")
        return {"reason": None}


class ActionSubmitAppointmentForm(Action):
    def name(self) -> str:
        return "action_submit_appointment_form"

    async def run(
            self, dispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Get all slots
        slots = {
            "date": tracker.get_slot("date"),
            "time": tracker.get_slot("time"),
            "doctor_name": tracker.get_slot("doctor_name"),
            "reason": tracker.get_slot("reason"),
        }

        try:
            result = appointment_mgr.create_appointment_from_slots(slots)
            dispatcher.utter_message(text=result["message"])
            return [SlotSet("appointment_id", result["appointment"]["id"])]
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn't complete your appointment booking: {str(e)}")
            return []