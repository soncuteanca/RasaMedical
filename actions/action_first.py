from typing import Dict, Any, Text, List
from rasa_sdk import Tracker, Action
from rasa_sdk.executor import CollectingDispatcher


class ActionGreetUser(Action):

    def name(self) -> Text:
        return "action_greet_user"

    def run(self, dispatcher: CollectingDispatcher,
            tracker: Tracker,
            domain: Dict[Text, Any]) -> List[Dict[Text, Any]]:
        dispatcher.utter_message(text="Hello, user!")

        return []
