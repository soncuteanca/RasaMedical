from typing import Dict, Any, Text, List
from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher
import json

class ActionGreetUser(Action):

    def name(self) -> Text:
        return "action_greet_user"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        
        try:
            # Get the user data from the session metadata
            session_metadata = tracker.get_slot("session_started_metadata")
            
            if not session_metadata or not isinstance(session_metadata, dict):
                dispatcher.utter_message(text="Hello, user!")
                return self._send_image(dispatcher)
            
            user_data_str = session_metadata.get('user')
            if not user_data_str:
                dispatcher.utter_message(text="Hello, user!")
                return self._send_image(dispatcher)
            
            try:
                user = json.loads(user_data_str)
                
                if not isinstance(user, dict):
                    dispatcher.utter_message(text="Hello, user!")
                    return self._send_image(dispatcher)
                
                name = user.get('name')
                if not name:
                    dispatcher.utter_message(text="Hello, user!")
                    return self._send_image(dispatcher)
                
                dispatcher.utter_message(text=f"Hello, {name}!")
                return self._send_image(dispatcher)
                
            except json.JSONDecodeError:
                dispatcher.utter_message(text="Hello, user!")
                return self._send_image(dispatcher)
                
        except Exception:
            dispatcher.utter_message(text="Hello, user!")
            return self._send_image(dispatcher)
    
    def _send_image(self, dispatcher: CollectingDispatcher) -> List[Dict[Text, Any]]:
        image_url = "https://i.imgur.com/0a8RIwP.png"
        dispatcher.utter_message(image=image_url)
        return []
