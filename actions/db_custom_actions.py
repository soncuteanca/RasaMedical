from typing import Dict, Text, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.db_connect import db_manager

class ActionAddPatient(Action):
    def name(self) -> Text:
        return "action_add_patient"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            # Get slot values
            name = tracker.get_slot("patient_name")
            surname = tracker.get_slot("patient_surname")
            age = tracker.get_slot("patient_age")
            medical_history = tracker.get_slot("medical_history")

            query = """
                INSERT INTO users (name, surname, age, medical_history)
                VALUES (%s, %s, %s, %s)
            """
            params = (name, surname, age, medical_history)
            
            db_manager.execute_query(query, params, fetch=False)
            dispatcher.utter_message(text=f"Patient {name} {surname} has been successfully added to the database.")
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I couldn't add the patient: {str(e)}")
        
        return []

class ActionSearchPatient(Action):
    def name(self) -> Text:
        return "action_search_patient"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            search_term = tracker.get_slot("search_term")
            
            query = """
                SELECT id, name, surname, age, medical_history 
                FROM users 
                WHERE name LIKE %s OR surname LIKE %s
            """
            params = (f"%{search_term}%", f"%{search_term}%")
            
            results = db_manager.execute_query(query, params)
            
            if results:
                response = f"Found {len(results)} patient(s) matching '{search_term}':\n"
                for row in results:
                    response += f"• {row['name']} {row['surname']} (Age: {row['age']})\n"
            else:
                response = f"No patients found matching '{search_term}'."
            
            dispatcher.utter_message(text=response)
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while searching: {str(e)}")
        
        return []
