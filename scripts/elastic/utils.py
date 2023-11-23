def get_user_yes_no(prompt: str) -> bool:
    user_input: str = ""
    while True:
        user_input = input(f"{prompt} [y/n]: ").lower()

        if user_input in ["y", "n"]:
            break

        print("Wrong answer")
    return user_input == "y"
