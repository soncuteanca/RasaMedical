from typing import Dict, Text, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.db_connect import db_manager

class ActionListDoctors(Action):
    def name(self) -> Text:
        return "action_list_doctors"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            query = """
                SELECT name, specialty 
                FROM doctors 
                ORDER BY specialty, name
            """
            results = db_manager.execute_query(query)
            
            if results:
                response_lines = ["Here are our doctors:"]
                current_specialty = None
                for doctor in results:
                    if doctor['specialty'] != current_specialty:
                        current_specialty = doctor['specialty']
                        if len(response_lines) > 1:
                            response_lines.append("")  # Blank line between specialties
                        response_lines.append(f"{current_specialty}:")
                    response_lines.append(f"  • {doctor['name']}")
                response = "\n".join(response_lines).strip()
            else:
                response = "No doctors found in the database."
            
            dispatcher.utter_message(text=response)
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while fetching doctors: {str(e)}")
        
        return []

class ActionListDoctorsBySpecialty(Action):
    def name(self) -> Text:
        return "action_list_doctors_by_specialty"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            specialty = tracker.get_slot("specialty")
            
            if not specialty:
                dispatcher.utter_message(text="Please specify which specialty you're interested in.")
                return []
            
            query = """
                SELECT name 
                FROM doctors 
                WHERE specialty = %s 
                ORDER BY name
            """
            results = db_manager.execute_query(query, (specialty,))
            
            if results:
                response_lines = [f"Here are our {specialty} doctors:"]
                for doctor in results:
                    response_lines.append(f"  • {doctor['name']}")
                response = "\n".join(response_lines).strip()
            else:
                response = f"No {specialty} doctors found in the database."
            
            dispatcher.utter_message(text=response)
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while fetching doctors: {str(e)}")
        
        return [] 