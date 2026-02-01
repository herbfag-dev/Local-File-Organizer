import reflex as rx

config = rx.Config(
    app_name="Local_File_Organizer",
    db_url="sqlite:///reflex.db",
    env=rx.Env.DEV,
)
