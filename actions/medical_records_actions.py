from typing import Dict, Text, Any, List
from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.db_connect import db_manager


class ActionViewMedicalRecords(Action):
    def name(self) -> Text:
        return "action_view_medical_records"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        try:
            # Try to get user from session - for now we'll use the first available user for demo
            # TODO: In production, get this from actual user authentication
            
            # First, let's find any user with medical records for demo purposes
            users_with_records_query = """
                SELECT DISTINCT u.id, u.first_name, u.last_name, COUNT(mr.id) as record_count
                FROM users u 
                INNER JOIN medical_records mr ON u.id = mr.patient_id 
                GROUP BY u.id, u.first_name, u.last_name
                ORDER BY record_count DESC
                LIMIT 1
            """
            user_info = db_manager.execute_query(users_with_records_query)
            
            if not user_info:
                # No users with records found, let's check if we have any users at all
                all_users_query = "SELECT id, first_name, last_name FROM users LIMIT 1"
                all_users = db_manager.execute_query(all_users_query)
                
                if all_users:
                    dispatcher.utter_message(text="You don't have any medical records yet. Your records will appear here after your appointments and consultations.\n\n💡 Tip: If you're testing the system, try running the test data setup script to create sample records.")
                else:
                    dispatcher.utter_message(text="No user accounts found. Please create an account first to view medical records.")
                return []
            
            user_id = user_info[0]['id']
            user_name = f"{user_info[0]['first_name']} {user_info[0]['last_name']}"
            
            query = """
                SELECT mr.*, d.name as doctor_name 
                FROM medical_records mr 
                LEFT JOIN doctors d ON mr.doctor_id = d.id 
                WHERE mr.patient_id = %s 
                ORDER BY mr.record_date DESC, mr.created_at DESC
                LIMIT 5
            """
            results = db_manager.execute_query(query, (user_id,))
            
            if results:
                response = f"Here are the recent medical records for {user_name}:\n\n"
                for record in results:
                    doctor_info = f" ({record['doctor_name']})" if record['doctor_name'] else ""
                    response += f"📋 **{record['title']}**{doctor_info}\n"
                    response += f"   📅 Date: {record['record_date']}\n"
                    response += f"   📝 Type: {record['record_type'].replace('_', ' ').title()}\n"
                    if record['description']:
                        response += f"   📄 Details: {record['description'][:100]}{'...' if len(record['description']) > 100 else ''}\n"
                    response += "\n"
                

            else:
                response = f"No medical records found for {user_name}. Records will appear here after appointments and consultations."
            
            dispatcher.utter_message(text=response)
            
        except Exception as e:
            dispatcher.utter_message(text=f"Sorry, I encountered an error while retrieving medical records: {str(e)}")
        
        return [] 