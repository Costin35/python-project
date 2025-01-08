from database import init_db
from logger import setup_logger
from Service import (add_show, list_shows, find_show, delete_show, change_score,
                     toggle_snooze, list_trailers, remaining_episodes, get_unwatched_shows,
                     find_youtube_trailers, start_continuous_uploads_search, list_uploads,
                     stop_continuous_uploads_search, find_youtube_uploads)

logger = setup_logger(log_filename="binge_watch.log")


def main():
    init_db()
    print("These are the top 5 shows from last year you haven't seen:")
    get_unwatched_shows()
    while True:
        print("\nTV Show Manager")
        print("1. Add a new show")
        print("2. List all shows")
        print("3. Find a show by IMDb link")
        print("4. Delete a show by ID")
        print("5. Change Score")
        print("6. Toggle Snooze")
        print("7. List all trailers")
        print("8. List all uploads")
        print("9. Remaining episodes")
        print("10. Find trailers")
        print("11. Find uploads")
        print("12. Start continuous uploads search")
        print("13. Stop continuous uploads search")
        print("14. Exit")
        choice = input("Choose an option: ")

        if choice == "1":
            add_show()
        elif choice == "2":
            list_shows()
        elif choice == "3":
            find_show()
        elif choice == "4":
            delete_show()
        elif choice == "5":
            change_score()
        elif choice == "6":
            toggle_snooze()
        elif choice == "7":
            list_trailers()
        elif choice == "8":
            list_uploads()
        elif choice == "9":
            remaining_episodes()
        elif choice == "10":
            find_youtube_trailers()
        elif choice == "11":
            find_youtube_uploads()
        elif choice == "12":
            start_continuous_uploads_search()
        elif choice == "13":
            stop_continuous_uploads_search()
        elif choice == "14":
            print("Goodbye!")
            logger.info("Application closed by user.")
            break
        else:
            print("Invalid choice. Please try again.")
            logger.warning(f"User entered invalid menu choice: {choice}")


if __name__ == "__main__":
    main()
