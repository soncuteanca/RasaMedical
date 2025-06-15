from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, FollowupAction
from rasa_sdk.types import DomainDict
from .appointment_manager import AppointmentManager

appointment_mgr = AppointmentManager()

class ActionBookAppointment(Action):
    def name(self) -> Text:
        return "action_book_appointment"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        try:
            # Get entities from current message
            entities = tracker.latest_message.get("entities", [])
            intent = tracker.latest_message.get("intent", {})
            
            # Check intent confidence
            if intent.get("confidence", 0) < 0.6:
                dispatcher.utter_message(text="I'm not sure I understood correctly. Could you please rephrase your request?")
                return [AllSlotsReset()]

            # Convert entities to slots
            current_slots = {}
            for entity in entities:
                current_slots[entity["entity"]] = entity["value"]
            
            # Get existing slots
            existing_slots = {
                "date": tracker.get_slot("date"),
                "time": tracker.get_slot("time"),
                "doctor_name": tracker.get_slot("doctor_name"),
                "reason": tracker.get_slot("reason")
            }
            
            # Merge slots (current entities override existing slots)
            final_slots = {**existing_slots, **current_slots}
            
            # Try to create appointment
            # Note: User context will be handled automatically by appointment manager
            result = appointment_mgr.create_appointment(final_slots)
            
            if result["success"]:
                dispatcher.utter_message(text=result["message"])
                return [
                    SlotSet("appointment_id", result["appointment"]["id"]),
                    AllSlotsReset()
                ]
            else:
                # Check if we need to activate form
                if "missing_slots" in result:
                    # Set the slots we do have
                    slot_events = [SlotSet(k, v) for k, v in final_slots.items() if v is not None]
                    
                    # Activate form to collect missing info
                    slot_events.append(FollowupAction("appointment_form"))
                    
                    dispatcher.utter_message(text=result["message"])
                    return slot_events
                else:
                    dispatcher.utter_message(text=result["message"])
                    return [AllSlotsReset()]

        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn't book your appointment: {str(e)}")
            return [AllSlotsReset()]

class ValidateAppointmentForm(FormValidationAction):
    def name(self) -> Text:
        return "validate_appointment_form"

    def validate_date(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate date slot."""
        try:
            if slot_value:
                normalized_date = appointment_mgr._normalize_date(slot_value)
                if normalized_date:
                    return {"date": normalized_date}
        except ValueError as e:
            dispatcher.utter_message(text=str(e))
            return {"date": None}
        
        dispatcher.utter_message(text="Please provide a valid date (e.g., tomorrow, Friday)")
        return {"date": None}

    def validate_time(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate time slot."""
        try:
            if slot_value:
                normalized_time = appointment_mgr._normalize_time(slot_value)
                if normalized_time:
                    return {"time": normalized_time}
        except ValueError as e:
            dispatcher.utter_message(text=str(e))
            return {"time": None}
        
        dispatcher.utter_message(text="Please provide a valid time (e.g., 2 PM, 14:00)")
        return {"time": None}

    def validate_doctor_name(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate doctor name slot."""
        try:
            # Check if this is a change request
            intent = tracker.latest_message.get("intent", {}).get("name")
            if intent == "provide_doctor":
                # Allow doctor changes during the form
                normalized_doctor = appointment_mgr._normalize_doctor_name(slot_value)
                if normalized_doctor:
                    dispatcher.utter_message(text=f"I'll update your appointment to see {normalized_doctor}")
                    return {"doctor_name": normalized_doctor}
            
            # Normal validation
            if slot_value:
                normalized_doctor = appointment_mgr._normalize_doctor_name(slot_value)
                if normalized_doctor:
                    return {"doctor_name": normalized_doctor}
        except ValueError as e:
            dispatcher.utter_message(text=str(e))
            return {"doctor_name": None}
        
        dispatcher.utter_message(text="Please specify which doctor you would like to see")
        return {"doctor_name": None}

    def validate_reason(
        self,
        slot_value: Any,
        dispatcher: CollectingDispatcher,
        tracker: Tracker,
        domain: DomainDict,
    ) -> Dict[Text, Any]:
        """Validate reason slot with enhanced validation."""
        if not slot_value:
            dispatcher.utter_message(text="What's the reason for your visit?")
            return {"reason": None}

        reason = str(slot_value).strip()
        
        # Check for very short reasons
        if len(reason) < 3:
            dispatcher.utter_message(text="Please provide a more detailed reason for your visit (at least 3 characters)")
            return {"reason": None}
            
        # Check for single character or punctuation only
        if len(reason) == 1 or reason.replace(".", "").strip() == "":
            dispatcher.utter_message(text="Please provide a meaningful reason for your visit")
            return {"reason": None}
            
        # Check for common invalid inputs
        invalid_inputs = [".", ",", "?", "!", "...", ".."]
        if reason in invalid_inputs:
            dispatcher.utter_message(text="Please provide a proper reason for your visit")
            return {"reason": None}
        
        return {"reason": reason}

class ActionSubmitAppointmentForm(Action):
    def name(self) -> Text:
        return "action_submit_appointment_form"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        # Get all slots
        slots = {
            "date": tracker.get_slot("date"),
            "time": tracker.get_slot("time"),
            "doctor_name": tracker.get_slot("doctor_name"),
            "reason": tracker.get_slot("reason"),
        }

        try:
            # Create appointment - user context handled automatically
            result = appointment_mgr.create_appointment(slots)
            dispatcher.utter_message(text=result["message"])
            return [
                SlotSet("appointment_id", result["appointment"]["id"]),
                AllSlotsReset()
            ]
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn't complete your appointment booking: {str(e)}")
            return [AllSlotsReset()]


class ActionViewAppointments(Action):
    def name(self) -> Text:
        return "action_view_appointments"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        try:
            # Get appointments from database - user context handled automatically
            result = appointment_mgr.get_appointments()
            
            if result["success"] and result["appointments"]:
                message_lines = ["📅 Your Appointments:"]
                for apt in result["appointments"]:
                    status_emoji = "✅" if apt["status"] == "scheduled" else "❌" if apt["status"] == "cancelled" else "✔️"
                    message_lines.append(
                        f"{status_emoji} {apt['date']} at {apt['time']} - {apt['doctor']}\n"
                        f"   Reason: {apt['reason']}"
                    )
                message = "\n".join(message_lines)
            else:
                message = "📅 You have no appointments scheduled."
            
            dispatcher.utter_message(text=message)
            return []

        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn't retrieve your appointments: {str(e)}")
            return []