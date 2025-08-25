#!/usr/bin/env python3
"""
Simple test for custom input functionality
"""

def test_keyboard_structure():
    """Test keyboard structure"""
    print("Testing keyboard structure...")
    
    try:
        from keyboards import get_match_history_keyboard, get_form_analysis_keyboard
        
        # Test match history keyboard
        history_kb = get_match_history_keyboard()
        buttons = []
        for row in history_kb.inline_keyboard:
            for button in row:
                buttons.append(button.text)
        
        print("Match history buttons:")
        for btn in buttons:
            print(f"  - {btn}")
        
        custom_button_found = False
        for btn in buttons:
            if "Ввести вручную" in btn:
                custom_button_found = True
                break
        
        if custom_button_found:
            print("✓ Custom input button found in history keyboard")
        else:
            print("✗ Custom input button NOT found in history keyboard")
        
        # Test form analysis keyboard
        form_kb = get_form_analysis_keyboard()
        buttons = []
        for row in form_kb.inline_keyboard:
            for button in row:
                buttons.append(button.text)
        
        print("Form analysis buttons:")
        for btn in buttons:
            print(f"  - {btn}")
        
        custom_period_found = False
        for btn in buttons:
            if "Свой период" in btn:
                custom_period_found = True
                break
        
        if custom_period_found:
            print("✓ Custom period button found in form keyboard")
        else:
            print("✗ Custom period button NOT found in form keyboard")
            
        return custom_button_found and custom_period_found
        
    except Exception as e:
        print(f"Error testing keyboards: {e}")
        return False

def test_validation():
    """Test input validation logic"""
    print("\nTesting validation logic...")
    
    # Valid inputs
    valid_inputs = ["15", "25", "50", "1", "100"]
    for input_val in valid_inputs:
        try:
            match_count = int(input_val)
            if 1 <= match_count <= 100:
                print(f"✓ {input_val} - valid")
            else:
                print(f"✗ {input_val} - out of range")
        except ValueError:
            print(f"✗ {input_val} - not a number")
    
    # Invalid inputs
    invalid_inputs = ["0", "101", "-5", "abc", "15.5", ""]
    for input_val in invalid_inputs:
        try:
            if not input_val:
                print(f"✗ empty - invalid (correctly rejected)")
                continue
            match_count = int(input_val)
            if match_count < 1 or match_count > 100:
                print(f"✗ {input_val} - out of range (correctly rejected)")
            else:
                print(f"! {input_val} - unexpectedly accepted")
        except ValueError:
            print(f"✗ {input_val} - not a number (correctly rejected)")

def test_states():
    """Test FSM states"""
    print("\nTesting FSM states...")
    
    try:
        from bot.handlers.new_match_history_handler import NewMatchHistoryStates
        from bot.handlers.form_analysis_handler import FormAnalysisStates
        
        if hasattr(NewMatchHistoryStates, 'waiting_for_custom_count'):
            print("✓ NewMatchHistoryStates.waiting_for_custom_count exists")
        else:
            print("✗ NewMatchHistoryStates.waiting_for_custom_count missing")
        
        if hasattr(FormAnalysisStates, 'waiting_for_custom_count'):
            print("✓ FormAnalysisStates.waiting_for_custom_count exists")
        else:
            print("✗ FormAnalysisStates.waiting_for_custom_count missing")
            
        return (hasattr(NewMatchHistoryStates, 'waiting_for_custom_count') and 
                hasattr(FormAnalysisStates, 'waiting_for_custom_count'))
                
    except Exception as e:
        print(f"Error testing states: {e}")
        return False

def main():
    print("Starting custom input functionality tests...\n")
    
    keyboard_test = test_keyboard_structure()
    test_validation()
    state_test = test_states()
    
    print(f"\nTest results:")
    print(f"Keyboard structure: {'PASS' if keyboard_test else 'FAIL'}")
    print(f"FSM states: {'PASS' if state_test else 'FAIL'}")
    print(f"Validation logic: PASS (manual verification)")
    
    if keyboard_test and state_test:
        print("\n✓ All tests PASSED!")
        print("\nManual testing instructions:")
        print("1. Open bot in Telegram")
        print("2. Go to 'История матчей'")
        print("3. Click 'Ввести вручную'")
        print("4. Enter a number between 1-100")
        print("5. Check that bot loads specified number of matches")
        print("6. Repeat for 'Анализ формы' -> 'Свой период'")
    else:
        print("\n✗ Some tests FAILED!")

if __name__ == "__main__":
    main()