def ask_user(question: str) -> str:
    """
    Asks the user a question directly during tool execution.
    Only active in interactive CLI sessions.
    """
    print(f"\n[Agent Question]: {question}")
    user_response = input("Your answer: ")
    return user_response
