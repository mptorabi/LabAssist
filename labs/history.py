import re
from collections import defaultdict
from decimal import Decimal, InvalidOperation, localcontext

NUMBER = re.compile(r"[+-]?(?:[0-9]+(?:\.[0-9]*)?|\.[0-9]+)\Z")


def numeric_value(text):
    text = text.strip()
    if not NUMBER.fullmatch(text):
        return None
    try:
        value = Decimal(text)
    except InvalidOperation:
        return None
    # Conservative plotting bounds; original text is always retained in the table.
    if not value.is_finite() or abs(value) > Decimal('1e12'):
        return None
    if value and abs(value) < Decimal('1e-12'):
        return None
    return value


def build_history(results):

    results = list(results)
    if len({(r.patient_id, r.lab_test_id) for r in results}) > 1:
        raise ValueError('History must contain one patient and one catalog test.')
    groups = defaultdict(list)
    rows = []
    for result in results:
        value = numeric_value(result.value)
        reason = ''
        if not result.unit.strip():
            reason = 'Not plotted: unit not recorded.'
        elif value is None:
            reason = 'Not plotted: not a supported plain decimal (or outside plotting bounds).'
        else:
            groups[result.unit].append((result, value))
        rows.append({'result': result, 'reason': reason})
    charts = []
    for unit, observations in sorted(groups.items()):
        observations.sort(key=lambda pair: (pair[0].test_date, pair[0].pk))
        if len(observations) < 2:
            charts.append({'unit': unit, 'points': [], 'count': 1})
            continue
        start = observations[0][0].test_date
        end = observations[-1][0].test_date
        low = min(v for _, v in observations)
        high = max(v for _, v in observations)
        points = []
        with localcontext() as context:
            context.prec = 60
            tick_values = [low] if low == high else [low, (low + high) / 2, high]
            ticks = []
            for value in tick_values:
                y = Decimal(140) if high == low else 220 - 160 * (value-low)/(high-low)
                label = format(value, '.6g')
                if Decimal(label) != value:
                    label = '~' + label
                ticks.append({'y': format(y, '.2f'), 'label': label})
            for result, value in observations:
                x = 360 if start == end else 140 + 440 * (result.test_date-start).days / (end-start).days
                y = Decimal(140) if high == low else 220 - 160 * (value-low)/(high-low)
                points.append({'x': format(x, '.2f'), 'y': format(y, '.2f'), 'result': result})
        charts.append({'unit': unit, 'points': points, 'count': len(observations),
                       'start': start, 'end': end, 'low': str(low), 'high': str(high),
                       'ticks': ticks, 'same_day': start == end})
    return {'history_rows': rows, 'history_charts': charts}