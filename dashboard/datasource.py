import datetime
import typesystem


user = typesystem.Schema(
    fields={
        "pk": typesystem.Integer(title="Identity", read_only=True),
        "username": typesystem.String(title="Username", max_length=100),
        "is_admin": typesystem.Boolean(title="Is Admin", default=False),
        "joined": typesystem.DateTime(title="Joined"),
    }
)


class Datasource:
    schema = user

    def __init__(
        self,
        filter: dict = None,
        search_term: str = "",
        order_by: str = None,
        reverse: bool = False,
        offset: int = None,
        limit: int = None,
    ):
        self._filter = filter
        self._search_term = search_term
        self._order_by = order_by
        self._reverse = reverse
        self._offset = offset
        self._limit = limit

    def copy(self, **kwargs):
        base_kwargs = {
            "filter": self._filter,
            "search_term": self._search_term,
            "order_by": self._order_by,
            "reverse": self._reverse,
            "offset": self._offset,
            "limit": self._limit,
        }
        base_kwargs.update(kwargs)
        return self.__class__(**base_kwargs)

    def search(self, search_term: str) -> "Datasource":
        return self.copy(search_term=search_term)

    def order_by(self, order_by: str) -> "Datasource":
        return self.copy(order_by=order_by)

    def offset(self, offset: int) -> "Datasource":
        return self.copy(offset=offset)

    def limit(self, limit: int) -> "Datasource":
        return self.copy(limit=limit)

    def filter(self, **filter) -> "Datasource":
        return self.copy(filter=filter)

    async def all(self):
        items = TABLES["users"]
        if self._filter is not None:
            for key, value in self._filter.items():
                items = [item for item in items if getattr(item, key) == value]
        if self._order_by is not None:
            items = sorted(
                items,
                key=lambda item: getattr(item, self._order_by),
                reverse=self._reverse,
            )
        if self._offset is not None:
            items = items[self._offset :]
        if self._limit is not None:
            items = items[: self._limit]
        return items

    async def get(self, **filter):
        items = await self.filter(**filter).all()
        return items[0] if items else None

    async def count(self) -> int:
        items = await self.all()
        return len(items)

    async def create(self, **kwargs):
        if "pk" not in kwargs:
            kwargs["pk"] = len(TABLES["users"])
        item = DataItem(**kwargs)
        TABLES["users"].insert(0, item)


class DataItem:
    def __init__(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)

    async def delete(self):
        TABLES["users"] = [item for item in TABLES["users"] if item.pk != self.pk]

    async def update(self, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)


TABLES = {
    "users": [
        DataItem(
            pk=i,
            username=f"tom{i}@tomchristie.com",
            is_admin=True,
            joined=datetime.datetime.now(),
        )
        for i in range(123)
    ]
}
