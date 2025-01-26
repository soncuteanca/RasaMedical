from rasa_sdk import Action, Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.db_connect import get_connection

class ActionFetchUsers(Action):
    def name(self) -> str:
        return "action_fetch_users"

    def run(self, dispatcher: CollectingDispatcher, tracker: Tracker, domain: dict):
        # Connect to the database
        connection = get_connection()
        try:
            cursor = connection.cursor()
            cursor.execute("SELECT id, name, surname, age FROM users")  # Simple SELECT query
            results = cursor.fetchall()

            # Format the response
            if results:
                response = "Here are the registered users:\n"
                for row in results:
                    response += f"ID: {row[0]}, Name: {row[1]} {row[2]}, Age: {row[3]}\n"
            else:
                response = "No users found in the database."

            # Send the response back to the user
            dispatcher.utter_message(response)
        except Exception as e:
            dispatcher.utter_message(text=f"An error occurred: {str(e)}")
        finally:
            connection.close()

        return []
