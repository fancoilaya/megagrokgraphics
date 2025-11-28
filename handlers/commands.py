# handlers/commands.py
"""
Central command registration hub for the MegaGrok Graphics Bot.
This returns a list of PTB20-compatible async handlers.
"""

from handlers.grokposter import get_handler as grokposter_handler


def get_handlers():
    """
    Return a list of CommandHandler objects.
    main.py will import this and attach them to the Application.
    """
    handlers = []

    # /grokposter (manual poster generation)
    handlers.append(grokposter_handler())

    # You can easily add more commands later:
    # from handlers.some_other_file import some_handler
    # handlers.append(some_handler())

    return handlers
