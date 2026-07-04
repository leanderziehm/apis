from . import api_001_events
from . import api_002_habits
from . import api_003_json
from . import api_004_measurements
from . import api_005_timers
# from . import api_006_llm
# from . import api_007_notify
# from . import api_008_quiz_answers


def register_all(ctx):
    api_001_events.register(ctx)
    api_002_habits.register(ctx)
    api_003_json.register(ctx)
    api_004_measurements.register(ctx)
    api_005_timers.register(ctx)
    # api_006_llm.register(ctx)
    # api_007_notify.register(ctx)
    # api_008_quiz_answers.register(ctx)
    