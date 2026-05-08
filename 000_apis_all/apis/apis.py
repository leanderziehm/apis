import apis.timer
import apis.habits


def register_all(ctx):
    apis.habits.register(ctx)
    apis.timer.register(ctx)