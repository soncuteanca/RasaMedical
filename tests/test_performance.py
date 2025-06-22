import time
import pytest
from unittest.mock import Mock, patch
from rasa_sdk import Tracker
from rasa_sdk.executor import CollectingDispatcher
from actions.medical_actions import ActionListDoctors


class TestPerformance:
    """Simple performance tests for critical actions"""
    
    def setup_method(self):
        self.dispatcher = Mock(spec=CollectingDispatcher)
        self.tracker = Mock(spec=Tracker)
        self.domain = {}

    @patch('actions.medical_actions.db_manager')
    def test_list_doctors_performance(self, mock_db_manager):
        """Test that listing doctors completes within acceptable time"""
        # Mock a reasonable database response
        mock_db_manager.execute_query.return_value = [
            {'name': f'Dr. Doctor{i}', 'specialty': 'Adult Cardiology'} 
            for i in range(10)
        ]
        
        action = ActionListDoctors()
        
        # Measure execution time
        start_time = time.time()
        result = action.run(self.dispatcher, self.tracker, self.domain)
        end_time = time.time()
        
        execution_time = end_time - start_time
        
        # Assert performance - should complete within 1 second
        assert execution_time < 1.0, f"Action took {execution_time:.2f}s, should be < 1.0s"
        
        # Verify it still works correctly
        assert result == []
        mock_db_manager.execute_query.assert_called_once()
        self.dispatcher.utter_message.assert_called_once()

    def test_mock_response_time(self):
        """Simple test to verify mocking doesn't add significant overhead"""
        start_time = time.time()
        
        # Simulate some basic operations
        mock_obj = Mock()
        mock_obj.some_method.return_value = "test"
        result = mock_obj.some_method()
        
        end_time = time.time()
        execution_time = end_time - start_time
        
        # Should be nearly instantaneous
        assert execution_time < 0.1, f"Mock operations took {execution_time:.3f}s"
        assert result == "test" 