from smart_book_seeker import ConversationManager

def main():
    conversation_manager = ConversationManager(strategy="iterative_top_k")
    while True:
        user_input = input("\033[93m>\033[0m ")
        if user_input == "exit":
            break
        for response in conversation_manager.route(message=user_input):
            print(f"\033[96m✦\033[0m {response}")
    print("\033[32m[對話結束]\033[0m")

if __name__ == "__main__":
    main()