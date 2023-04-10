import dataclasses
import re
from typing import List, Dict, Set

from tg_filtering_bot.crud.dto import UserFilterDTO, QueueMessageDTO
from tg_filtering_bot.crud.schema import UserId


@dataclasses.dataclass
class FilterGroup:
    regexp: re.Pattern
    users: Set[UserId]


def _build_matchers(filters: List[UserFilterDTO]) -> List[FilterGroup]:
    result: Dict[str, FilterGroup] = {}

    for f in filters:
        if f.filter_ in result:
            result[f.filter_].users.add(f.user_id)
        else:
            result[f.filter_] = FilterGroup(
                regexp=re.compile(f.filter_, flags=re.IGNORECASE),
                users={f.user_id}
            )
    return list(result.values())


def match_user_filters(message: QueueMessageDTO, filters: List[UserFilterDTO]) -> Set[UserId]:
    matchers = _build_matchers(filters)

    result = set()

    for m in matchers:
        if m.regexp.search(message.message):
            result.update(m.users)

    return result
