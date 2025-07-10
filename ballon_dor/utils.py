from django.utils import timezone
from datetime import datetime
from .models import Candidate
from django.db.models import Max
import pytz


def get_active_year():
    max_year = Candidate.objects.aggregate(Max("year"))["year__max"]
    return max_year if max_year else timezone.now().year


def get_voting_deadline(year):
    return datetime(year, 9, 21, 23, 59, 59, tzinfo=pytz.UTC)
