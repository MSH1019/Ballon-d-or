from django.utils import timezone
from datetime import datetime
from .models import Candidate
from django.db.models import Max
import pytz


def get_active_year():
    max_year = Candidate.objects.aggregate(Max("year"))["year__max"]
    return max_year if max_year else timezone.now().year


# Years with a non-default deadline. 2026 closes the day before the ceremony (Oct 26, London).
VOTING_DEADLINES = {
    2026: datetime(2026, 10, 25, 23, 59, 59, tzinfo=pytz.UTC),
}


def get_voting_deadline(year):
    default = datetime(year, 9, 21, 23, 59, 59, tzinfo=pytz.UTC)
    return VOTING_DEADLINES.get(year, default)
