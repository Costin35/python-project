from tmdbv3api import TMDb, TV, Search, Season, Discover
from sqlalchemy.exc import IntegrityError
from datetime import date, timedelta
import requests
import pytz
from database import Session, Show, Trailer, Upload
from logger import setup_logger
from apscheduler.schedulers.background import BackgroundScheduler


logger = setup_logger(log_filename="binge_watch.log")
scheduler = BackgroundScheduler()
tmdb = TMDb()
tmdb.api_key = "5a185f598d032174549633cddded6891"
tv = TV()
search = Search()
season_api = Season()
discover = Discover()


def add_show():
    """
   Prompt the user for the details of a show and add it to the database.

   Steps:
       1. Ask for user input (name, IMDB link, last watched season, last watched episode, last watched date, score).
       2. Create a new Show object and attempt to commit it to the database.
       3. If successful print confirmation and log the added show.
       4. Handle IntegrityError if the IMDb link must be unique.
       5. Handle ValueError if the user provides invalid numerical input.

   Exceptions:
       IntegrityError: If the user attempts to add a show with a duplicate IMDb link.
       ValueError: If season, episode or score are not valid numbers.
   """
    session = Session()
    try:
        name = input("Enter the name of the show: ")
        imdb_link = input("Enter the IMDB link: ")
        last_watched_season = int(input("Enter the last watched season: "))
        last_watched_episode = int(input("Enter the last watched episode: "))
        last_watched_date = input("Enter the last watched date (YYYY-MM-DD or leave blank): ") or None
        score = float(input("Enter your score for the show (1-10): ") or 0.0)

        new_show = Show(
            name=name,
            imdb_link=imdb_link,
            last_watched_season=last_watched_season,
            last_watched_episode=last_watched_episode,
            last_watched_date=last_watched_date,
            score=score
        )
        session.add(new_show)
        session.commit()
        print("Show added successfully!")
        logger.info(f"Added new show {new_show.name}")

    except IntegrityError as e:
        session.rollback()
        print("Error: IMDb link must be unique.")
        logger.error(f"Failed to add show: IntegrityError -> {e}")

    except ValueError as e:
        session.rollback()
        print("Invalid input for season/episode or score.")
        logger.warning(f"ValueError while adding show. Details: {e}")

    finally:
        session.close()


def list_shows():
    """
    Retrieve and print all shows stored in the database.

    Steps:
        1. Query the Show table for all shows.
        2. If none found print a message and log that no shows exist.
        3. Otherwise, print each show's details (ID, name, IMDB link, last watched season,
                                                last watched episode, last watched date, score).
        4. Log the count of listed shows.
    """
    session = Session()
    try:
        shows = session.query(Show).all()
        if not shows:
            print("No shows found.")
            logger.info("Tried to list shows but none found.")
            return

        for show in shows:
            print(f"""
            ID: {show.id}
            Name: {show.name}
            IMDb Link: {show.imdb_link}
            Last Watched Season: {show.last_watched_season}
            Last Watched Episode: {show.last_watched_episode}
            Last Watched Date: {show.last_watched_date}
            Score: {show.score}
            Snoozed: {'Yes' if show.snoozed else 'No'}
            """)

        logger.info(f"Listed {len(shows)} show(s).")
    finally:
        session.close()


def find_show():
    """
    Prompt for an IMDB link and display the show that matches it, if any.

    Steps:
        1. Ask the user for an IMDB link.
        2. Query the database for a show with that link.
        3. If found print its details otherwise indicate that none was found.
        4. Log the success or failure of the search.
    """
    session = Session()
    try:
        imdb_link = input("Enter the IMDB link to search for: ")
        show = session.query(Show).filter_by(imdb_link=imdb_link).first()

        if not show:
            print("No show found with that IMDb link.")
            logger.info(f"No show found with IMDb link = {imdb_link}")
            return

        print(f"""
        ID: {show.id}
        Name: {show.name}
        IMDB Link: {show.imdb_link}
        Last Watched Season: {show.last_watched_season}
        Last Watched Episode: {show.last_watched_episode}
        Last Watched Date: {show.last_watched_date}
        Score: {show.score}
        Snoozed: {'Yes' if show.snoozed else 'No'}
        """)
        logger.info(f"Found show with IMDb link = {imdb_link}")
    finally:
        session.close()


def delete_show():
    """
    Prompt for a show ID then delete the corresponding show from the database.

    Steps:
        1. Ask the user for the show ID to delete.
        2. Find the show by ID and if it exists delete it.
        3. Commit the transaction and log the deletion.
        4. If no show is found inform the user and log the attempt.
    """
    session = Session()
    try:
        show_id = int(input("Enter the ID of the show to delete: "))
        show = session.query(Show).get(show_id)

        if not show:
            print("No show found with that ID.")
            logger.info(f"Attempted to delete show ID={show_id}, but not found.")
            return

        show_name = show.name
        session.delete(show)
        session.commit()
        print(f"Show {show_name} deleted successfully.")
        logger.info(f"Deleted show ID={show_id}.")
    finally:
        session.close()


def change_score():
    """
   Prompt for a show ID and a new score and update the show's score in the database.

   Steps:
       1. Ask the user for the show ID to modify.
       2. Query the show by ID.
       3. If found set its new score commit the transaction and log the update.
       4. If not found inform the user and log the attempt.
   """
    session = Session()
    try:
        show_id = int(input("Enter the ID of the show to change: "))
        show = session.query(Show).get(show_id)

        if not show:
            print("No show found with that ID.")
            logger.info(f"No show found for ID={show_id} when trying to change score.")
            return

        new_score = input("Enter the new score: ")
        show.score = new_score
        session.commit()
        print("Show score changed successfully.")
        logger.info(f"Show ID={show_id} score changed to {new_score}.")
    finally:
        session.close()


def toggle_snooze():
    """
    Prompt for a show ID, then toggle its snooze status (snoozed/unsnoozed).

    Steps:
        1. Ask the user for the show ID to modify.
        2. Retrieve the show
        3. If found toggle its 'snoozed' boolean.
        4. Commit the transaction and print a success message.
        5. If not found inform the user and log the attempt.
    """
    session = Session()
    try:
        show_id = int(input("Enter the ID of the show to change: "))
        show = session.query(Show).get(show_id)

        if not show:
            print("No show found with that ID.")
            logger.info(f"No show found for ID={show_id} when toggling snooze.")
            return

        if show.snoozed:
            show.snoozed = False
            session.commit()
            print(f"Show {show.name} unsnoozed successfully.")
            logger.info(f"Show ID={show_id} unsnoozed.")
        else:
            show.snoozed = True
            session.commit()
            print(f"Show {show.name} snoozed successfully.")
            logger.info(f"Show ID={show_id} snoozed.")
    finally:
        session.close()


def list_trailers():
    """
    List all trailers found in the database.

    Steps:
        1. Query the Trailer table for all trailers.
        2. If none are found inform the user.
        3. Otherwise, print each trailer's details.
    """
    session = Session()
    try:
        trailers = session.query(Trailer).all()
        if not trailers:
            print("No trailers found.")
            return

        for trailer in trailers:
            print(f"""
            ID: {trailer.id}
            Show ID: {trailer.show_id}
            URL: {trailer.url}
            Is New: {'Yes' if trailer.is_new else 'No'}
            """)
    finally:
        session.close()


def list_uploads():
    """
    List all uploads found in the database.

    Steps:
        1. Query the Upload table for all uploads.
        2. If none are found inform the user.
        3. Otherwise, print each upload's details.
    """
    session = Session()
    try:
        uploads = session.query(Upload).all()
        if not uploads:
            print("No uploads found.")
            return

        for upload in uploads:
            print(f"""
            ID: {upload.id}
            Show ID: {upload.show_id}
            Name: {upload.name}
            URL: {upload.url}
            Is New: {'Yes' if upload.is_new else 'No'}
            """)
    finally:
        session.close()


def get_unwatched_shows():
    """
    Display the first 5 top-rated TV series from TMDb (with constraints) that are not in local DB.

    Steps:
        1. Query local database for existing shows.
        2. Use Discover from TMDB to find top-rated shows in the last year.
        3. Print the names and rating of up to 5 shows that are not in the local database.
    """
    session = Session()
    existing_shows = {show.name for show in session.query(Show).all()}
    one_year_ago = date.today() - timedelta(days=365)
    one_year_ago_str = one_year_ago.isoformat()
    try:
        top_shows = discover.discover_tv_shows(
            {
                "first_air_date": one_year_ago_str,
                "sort_by": "vote_average.desc",
                "vote_count.gte": 50
            }
        )
        index = 0
        for show in top_shows:
            if index >= 5:
                break
            if show.name not in existing_shows:
                index = index + 1
                print(f"{show.name} (Rating: {show.vote_average})")
    finally:
        session.close()


def remaining_episodes():
    """
    Show the remaining unwatched episodes for each show in the local database.

    Steps:
        1. For each show in the database that is not snoozed:
            - Search for the show by name on TMDB.
            - Retrieve details for each season.
            - Print any episodes by season & episode number not watched yet.
    """
    session = Session()
    existing_shows = session.query(Show).all()

    try:
        for show in existing_shows:
            if not show.snoozed:
                results = search.tv_shows(show.name)

                found_show = results[0]
                found_show_id = found_show.id
                found_show_details = tv.details(found_show_id)

                print(f"For show: {show.name}")

                for season in found_show_details.seasons:
                    if season.season_number >= show.last_watched_season:
                        season_details = season_api.details(found_show_id, season.season_number)

                        for episode in season_details.episodes:
                            if (
                                    season.season_number == show.last_watched_season
                                    and episode.episode_number <= show.last_watched_episode
                            ):
                                continue

                            print(
                                f"Season: {season.season_number} Episode: {episode.episode_number}   {episode.name}"
                            )
    finally:
        session.close()


def find_youtube_trailers():
    """
    Prompt for a show name then fetch up to 5 YouTube trailers related to that show.

    Steps:
        1. Ask for the show name and try to find it in the database.
        2. If found query the YouTube API for up to 5 trailer videos.
        3. Add each found trailer (if not already in the database) to the Trailer table.
        4. Notify new uploads after each addition.
    """
    session = Session()

    try:
        show_name = input("Enter the name of the show for which to find trailers: ")
        show = session.query(Show).filter_by(name=show_name).first()

        if not show:
            print("No show found with that name.")
            logger.info(f"No show found for name {show_name} when trying to find trailers.")
            return

        query = f"{show_name} trailer"
        youtube_url = (f"https://www.googleapis.com/youtube/v3/search?q={query}"
                       f"&key=AIzaSyBKI6AfPwvYNAPyRHV1hCPoU0g9fMFkGMQ&part=snippet&type=video")
        try:
            youtube_response = requests.get(youtube_url).json()
        except Exception as e:
            logger.error(f"Error calling youtube API for show {show.name}: {e}")

        for index, item in enumerate(youtube_response.get('items', [])):
            if index >= 5:
                break

            video_id = item['id']['videoId']
            url = f"https://www.youtube.com/watch?v={video_id}"
            if not session.query(Trailer).filter_by(show_id=show.id, url=url).first():
                new_trailer = Trailer(show_id=show.id, url=url, is_new=True)
                session.add(new_trailer)
                session.commit()

        notify_new_uploads()
    finally:
        session.close()


def start_continuous_uploads_search():
    """
    Schedule continuous background searches for new trailers and uploads every 60 seconds.

    Steps:
        1. Adds two jobs to the APScheduler:
           - search_trailers_for_all_shows
           - search_uploads_for_all_shows
        2. Both jobs run every 60 seconds.
        3. Starts the scheduler and logs that it's running.
    """
    scheduler.add_job(
        func=search_trailers_for_all_shows,
        trigger="interval",
        seconds=60,
        id="continuous_trailer_search",
        replace_existing=True,
        timezone=pytz.utc
    )
    scheduler.add_job(
        func=search_uploads_for_all_shows,
        trigger="interval",
        seconds=60,
        id="continuous_upload_search",
        replace_existing=True,
        timezone=pytz.utc
    )
    scheduler.start()
    print("Started continuous uploads search")
    logger.info("Continuous uploads search job started")


def stop_continuous_uploads_search():
    """
    Stop the continuous background searches for new trailers and uploads.

    Steps:
        1. Remove both scheduled jobs (trailers and uploads).
        2. Log the shutdown.
    """
    scheduler.remove_job("continuous_trailer_search")
    scheduler.remove_job("continuous_upload_search")
    print("Stopped continuous uploads search")
    logger.info("Stopped continuous uploads search job")


def search_trailers_for_all_shows():
    """
    Search YouTube for new trailers for each show in the database.

    Steps:
        1. Retrieve all shows from the database.
        2. For each show query YouTube (sorted by date) looking for the most recent trailers.
        3. If a new trailer is found add it to the Trailer table with field is_new=True.
        4. Commit after each new trailer then call notify_new_uploads.
    """
    session = Session()
    try:
        shows = session.query(Show).all()
        if not shows:
            logger.info("No shows found in database when searching for trailers")
            return

        for show in shows:
            query = f"{show.name} trailer"
            youtube_url = (f"https://www.googleapis.com/youtube/v3/search?q={query}"
                           f"&key=AIzaSyBKI6AfPwvYNAPyRHV1hCPoU0g9fMFkGMQ&part=snippet&type=video&order=date")
            try:
                youtube_response = requests.get(youtube_url).json()
            except Exception as e:
                logger.error(f"Error calling youtube API for show {show.name}: {e}")

            for item in youtube_response.get('items', []):
                video_id = item['id']['videoId']
                url = f"https://www.youtube.com/watch?v={video_id}"

                existing_trailer = session.query(Trailer).filter_by(show_id=show.id, url=url).first()
                if not existing_trailer:
                    new_trailer = Trailer(show_id=show.id, url=url, is_new=True)
                    session.add(new_trailer)
                    logger.info(f"New trailer for show {show.name} added to database")
                    break
            session.commit()

            notify_new_uploads()
    finally:
        session.close()


def notify_new_uploads():
    """
    Check if there are any new trailers or uploads in the database and print and log them.

    Steps:
        1. Find all trailers and uploads with field is_new=True.
        2. Print and log each new trailer or upload.
        3. Mark them as is_new=False and commit the change.
        4. If none are found log that nothing new is present.
    """
    session = Session()
    try:
        new_trailers = session.query(Trailer).filter_by(is_new=True).all()
        new_uploads = session.query(Upload).filter_by(is_new=True).all()
        if not new_trailers or not new_uploads:
            logger.info("No new uploads found.")
            return
        for trailer in new_trailers:
            show_name = session.query(Show).filter_by(id=trailer.show_id).first().name
            print(f"\nNew trailer for show {show_name} at url {trailer.url}")
            logger.info(f"New trailer for show {show_name} at url {trailer.url}")

            trailer.is_new = False
        for upload in new_uploads:
            show_name = session.query(Show).filter_by(id=upload.show_id).first().name
            print(f"\nNew upload for show {show_name} about episode {upload.name} at url {upload.url}")
            logger.info(f"New upload for show {show_name} about episode{upload.name} at url {upload.url}")

            upload.is_new = False

        session.commit()
    finally:
        session.close()


def find_youtube_uploads():
    """
    Prompt for a show name and episode then fetch up to 5 YouTube videos about that episode.

    Steps:
        1. Ask for the show name (find it in database).
        2. Ask for the episode name.
        3. Query YouTube for up to 5 videos matching "show_name + episode name".
        4. Add each one to the Upload table if it's new then call notify_new_uploads.
    """
    session = Session()
    try:
        show_name = input("Enter the name of the show: ")
        show = session.query(Show).filter_by(name=show_name).first()

        if not show:
            print("No show found with that name.")
            logger.info(f"No show found for name {show_name} when trying to find trailers.")
            return

        query = input("Enter the name of the episode: ")
        youtube_url = (f"https://www.googleapis.com/youtube/v3/search?q={show_name}{query}"
                       f"&key=AIzaSyBKI6AfPwvYNAPyRHV1hCPoU0g9fMFkGMQ&part=snippet&type=video")
        try:
            youtube_response = requests.get(youtube_url).json()
        except Exception as e:
            logger.error(f"Error calling youtube API for show {show.name}: {e}")

        for index, item in enumerate(youtube_response.get('items', [])):
            if index >= 5:
                break

            video_id = item['id']['videoId']
            url = f"https://www.youtube.com/watch?v={video_id}"
            if not session.query(Upload).filter_by(show_id=show.id, url=url).first():
                new_upload = Upload(show_id=show.id, name=query, url=url, is_new=True)
                session.add(new_upload)
                session.commit()

        notify_new_uploads()
    finally:
        session.close()


def search_uploads_for_all_shows():
    """
    Continuously search for new YouTube uploads (sorted by date) related to each show's known uploads.

    Steps:
        1. Retrieve all shows from database.
        2. For each show retrieve existing uploads.
        3. Query YouTube for up-to-date videos regarding "show_name + episode_name".
        4. If new videos are found add them as 'Upload' with field is_new=True.
        5. Commit after each new upload then call notify_new_uploads.
    """
    session = Session()
    try:
        shows = session.query(Show).all()
        if not shows:
            logger.info("No shows found in database when searching for trailers")
            return
        for show in shows:
            uploads = session.query(Upload).filter_by(show_id=show.id).all()
            for upload in uploads:
                query = f"{show.name}{upload.name}"
                youtube_url = (f"https://www.googleapis.com/youtube/v3/search?q={query}"
                               f"&key=AIzaSyBKI6AfPwvYNAPyRHV1hCPoU0g9fMFkGMQ&part=snippet&type=video&order=date")
                try:
                    youtube_response = requests.get(youtube_url).json()
                except Exception as e:
                    logger.error(f"Error calling youtube API for show {show.name}: {e}")

                for item in youtube_response.get('items', []):
                    video_id = item['id']['videoId']
                    url = f"https://www.youtube.com/watch?v={video_id}"

                    existing_upload = session.query(Upload).filter_by(show_id=show.id, url=url).first()
                    if not existing_upload:
                        new_upload = Upload(show_id=show.id, name=upload.name, url=url, is_new=True)
                        session.add(new_upload)
                        logger.info(f"New upload for show {show.name} episode {upload.name} added to database")
                        break
            session.commit()

            notify_new_uploads()
    finally:
        session.close()
