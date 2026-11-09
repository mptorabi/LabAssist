"""Offline structural review gate. Never imports candidates or verifies clinical truth."""
from urllib.parse import urlsplit


def validate_proposals(data):
    """Return errors; human source review remains mandatory even when this passes."""
    if not isinstance(data, dict) or set(data) != {'schema_version', 'proposals'}:
        return ['Expected schema_version and proposals only.']
    if type(data['schema_version']) is not int or data['schema_version'] != 1:
        return ['schema_version must be 1.']
    proposals = data['proposals']
    if not isinstance(proposals, list) or not 1 <= len(proposals) <= 100:
        return ['proposals must contain 1 to 100 items.']
    errors, codes = [], set()
    fields = {'code', 'name', 'specimen', 'method', 'source_url', 'source_title',
              'source_excerpt', 'accessed_on', 'reviewed_by', 'reviewed_on', 'decision'}
    from datetime import date
    for index, item in enumerate(proposals, 1):
        prefix = f'Proposal {index}: '
        if not isinstance(item, dict) or set(item) != fields:
            errors.append(prefix + 'unexpected or missing fields.')
            continue
        if any(not isinstance(v, str) or len(v) > 4000 for v in item.values()):
            errors.append(prefix + 'fields must be strings of at most 4000 characters.')
            continue
        for field in fields - {'specimen', 'method'}:
            if not item[field].strip():
                errors.append(prefix + field + ' is required.')
        code = item['code'].strip().casefold()
        if code in codes:
            errors.append(prefix + 'duplicate code.')
        codes.add(code)
        try:
            url = urlsplit(item['source_url'])
            if url.scheme != 'https' or not url.hostname or url.username or url.password:
                raise ValueError
        except ValueError:
            errors.append(prefix + 'source_url must be a public HTTPS reference without credentials.')
        dates = {}
        for field in ['accessed_on', 'reviewed_on']:
            try:
                dates[field] = date.fromisoformat(item[field])
                if dates[field] > date.today():
                    raise ValueError
            except ValueError:
                errors.append(prefix + field + ' must be a non-future ISO date.')
        if len(dates) == 2 and dates['reviewed_on'] < dates['accessed_on']:
            errors.append(prefix + 'review cannot predate source access.')
        if item['decision'] != 'accepted':
            errors.append(prefix + 'explicit accepted decision required.')
    return errors
