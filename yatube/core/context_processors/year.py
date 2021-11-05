import datetime as dt


def year(request):
    current_date = dt.date.today()
    current_year = int(current_date.year)
    return {'year': current_year}
