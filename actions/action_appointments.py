from typing import Any, Dict, List, Text
from rasa_sdk import Action, Tracker, FormValidationAction
from rasa_sdk.executor import CollectingDispatcher
from rasa_sdk.events import SlotSet, AllSlotsReset, FollowupAction
from rasa_sdk.types import DomainDict
from .appointment_manager import AppointmentManager
import json

appointment_mgr = AppointmentManager()

def _extract_user_id_from_tracker(tracker: Tracker) -> int:
    """Extract user ID from tracker metadata"""
    try:
        # Try to get user data from session metadata
        session_metadata = tracker.get_slot("session_started_metadata")
        if session_metadata and isinstance(session_metadata, dict):
            user_data_str = session_metadata.get('user')
            if user_data_str:
                user = json.loads(user_data_str)
                if isinstance(user, dict) and 'id' in user:
                    return int(user['id'])
        
        # Fallback: try to get from latest message metadata
        latest_message = tracker.latest_message
        if latest_message and 'metadata' in latest_message:
            metadata = latest_message['metadata']
            if 'user' in metadata:
                user_data_str = metadata['user']
                if user_data_str:
                    user = json.loads(user_data_str)
                    if isinstance(user, dict) and 'id' in user:
                        return int(user['id'])
        
        # If no user ID found, raise an error
        raise ValueError("User ID not found in session")
        
    except Exception as e:
        print(f"Error extracting user ID: {e}")
        raise ValueError("Could not extract user ID from session")

class ActionBookAppointment(Action):
    def name(self) -> Text:
        return "action_book_appointment"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        try:
            # Extract and set user ID from tracker
            user_id = _extract_user_id_from_tracker(tracker)
            appointment_mgr.set_user_id(user_id)
            
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
                # Get the date from the tracker to validate working hours
                date_slot = tracker.get_slot("date")
                normalized_time = appointment_mgr._normalize_time(slot_value, date_slot)
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
        
        # Check if this is a symptom intent during the form
        intent = tracker.latest_message.get("intent", {}).get("name")
        if intent == "report_symptom_intent":
            # Extract the symptom text as the reason
            symptom_text = tracker.latest_message.get("text", "").strip()
            if symptom_text:
                return {"reason": symptom_text}
        
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
        try:
            # Extract and set user ID from tracker
            user_id = _extract_user_id_from_tracker(tracker)
            appointment_mgr.set_user_id(user_id)
            
            # Get all slots
            slots = {
                "date": tracker.get_slot("date"),
                "time": tracker.get_slot("time"),
                "doctor_name": tracker.get_slot("doctor_name"),
                "reason": tracker.get_slot("reason")
            }
            
            # Create appointment
            result = appointment_mgr.create_appointment(slots)
            
            if result["success"]:
                dispatcher.utter_message(text=result["message"])
                return [
                    SlotSet("appointment_id", result["appointment"]["id"]),
                    AllSlotsReset()
                ]
            else:
                dispatcher.utter_message(text=result["message"])
                return [AllSlotsReset()]
                
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
            # Extract and set user ID from tracker
            user_id = _extract_user_id_from_tracker(tracker)
            appointment_mgr.set_user_id(user_id)
            
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


class ActionCancelAppointment(Action):
    def name(self) -> Text:
        return "action_cancel_appointment"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        try:
            # Extract and set user ID from tracker
            user_id = _extract_user_id_from_tracker(tracker)
            appointment_mgr.set_user_id(user_id)
            
            # Get appointments from database
            result = appointment_mgr.get_appointments()
            
            if result["success"] and result["appointments"]:
                # Get the most recent appointment to cancel
                active_appointments = [apt for apt in result["appointments"] if apt["status"] == "scheduled"]
                
                if active_appointments:
                    # For simplicity, cancel the most recent appointment
                    # In a real system, you'd ask which specific appointment to cancel
                    latest_apt = active_appointments[0]
                    
                    # Cancel the appointment
                    cancel_result = appointment_mgr.cancel_appointment(latest_apt["id"])
                    
                    if cancel_result["success"]:
                        dispatcher.utter_message(
                            text=f"✅ Your appointment on {latest_apt['date']} at {latest_apt['time']} with {latest_apt['doctor']} has been cancelled."
                        )
                    else:
                        dispatcher.utter_message(text=f"❌ Sorry, I couldn't cancel your appointment: {cancel_result['message']}")
                else:
                    dispatcher.utter_message(text="📅 You have no active appointments to cancel.")
            else:
                dispatcher.utter_message(text="📅 You have no appointments to cancel.")
            
            return []
                
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn't cancel your appointment: {str(e)}")
            return []


class ActionModifyAppointment(Action):
    def name(self) -> Text:
        return "action_modify_appointment"

    async def run(
        self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]
    ) -> List[Dict[Text, Any]]:
        try:
            # Extract and set user ID from tracker
            user_id = _extract_user_id_from_tracker(tracker)
            appointment_mgr.set_user_id(user_id)
            
            # Get appointments from database
            result = appointment_mgr.get_appointments()
            
            if result["success"] and result["appointments"]:
                # Get the most recent appointment to modify
                active_appointments = [apt for apt in result["appointments"] if apt["status"] == "scheduled"]
                
                if active_appointments:
                    latest_apt = active_appointments[0]
            
                    # Get entities from current message for modification
                    entities = tracker.latest_message.get("entities", [])
                    modifications = {}
                    
                    for entity in entities:
                        if entity["entity"] in ["date", "time", "doctor_name", "reason"]:
                            modifications[entity["entity"]] = entity["value"]
                    
                    if modifications:
                        # Apply modifications
                        modify_result = appointment_mgr.modify_appointment(latest_apt["id"], modifications)
                        
                        if modify_result["success"]:
                            dispatcher.utter_message(text=modify_result["message"])
                        else:
                            dispatcher.utter_message(text=f"❌ Sorry, I couldn't modify your appointment: {modify_result['message']}")
                    else:
                        # No specific modifications provided, ask what they want to change
                        dispatcher.utter_message(
                            text=f"What would you like to change about your appointment on {latest_apt['date']} at {latest_apt['time']} with {latest_apt['doctor']}?"
                        )
                else:
                    dispatcher.utter_message(text="📅 You have no active appointments to modify.")
            else:
                dispatcher.utter_message(text="📅 You have no appointments to modify.")
            
            return []
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn't modify your appointment: {str(e)}")
            return []