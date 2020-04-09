import datetime
import typesystem
import typing


user = typesystem.Schema(
    fields={
        "pk": typesystem.Integer(title="Identity", read_only=True),
        "username": typesystem.String(title="Username", max_length=100),
        "is_admin": typesystem.Boolean(title="Is Admin", default=False),
        "joined": typesystem.DateTime(title="Joined"),
    }
)


def autoincrement():
    """
    Returns an autoincrmenting callable.
    Useful for working with mock datasources.

    For example:

    schema = typesystem.Schema(fields = {
        "pk": typesystem.Integer(title="ID", read_only=True, default=autoincrement()),
        ...
    })
    """
    i = 0

    def func():
        nonlocal i
        ret = i
        i += 1
        return ret

    return func


class DataSource:
    def search(self, search_term: str) -> "DataSource":
        raise NotImplementedError()

    def filter(self, **filter: typing.Any) -> "DataSource":
        raise NotImplementedError()

    def order_by(self, order_by: str) -> "DataSource":
        raise NotImplementedError()

    def offset(self, offset: int) -> "DataSource":
        raise NotImplementedError()

    def limit(self, limit: int) -> "DataSource":
        raise NotImplementedError()

    async def count(self) -> int:
        raise NotImplementedError()

    async def all(self) -> typing.List["DataItem"]:
        raise NotImplementedError()

    async def get(self, **filter: typing.Any) -> typing.Optional["DataItem"]:
        raise NotImplementedError()

    async def create(self, **kwargs) -> "DataItem":
        raise NotImplementedError()


class DataItem:
    async def delete(self):
        raise NotImplementedError()

    async def update(self, **kwargs):
        raise NotImplementedError()


class MockDataSource(DataSource):
    def __init__(
        self,
        schema,
        initial: typing.List[dict] = None,
        _search_term: str = None,
        _filter_kwargs: dict = None,
        _order_by: str = None,
        _offset: int = None,
        _limit: int = None,
    ):
        self.schema = schema
        self._items = [] if initial is None else initial
        self._search_term = _search_term
        self._filter_kwargs = _filter_kwargs
        self._order_by = _order_by
        self._offset = _offset
        self._limit = _limit

        for item in self._items:
            for key, field in self.schema.fields.items():
                if key not in item and field.has_default():
                    item[key] = field.get_default_value()

    def _copy(self, **kwargs: typing.Any) -> "MockDataSource":
        base_kwargs = {
            "schema": self.schema,
            "initial": self._items,
            "_search_term": self._search_term,
            "_filter_kwargs": self._filter_kwargs,
            "_order_by": self._order_by,
            "_offset": self._offset,
            "_limit": self._limit,
        }
        base_kwargs.update(kwargs)
        return self.__class__(**base_kwargs)

    def search(self, search_term: str) -> "MockDataSource":
        return self._copy(_search_term=search_term)

    def filter(self, **kwargs) -> "MockDataSource":
        kwargs = {
            key: self.schema.fields[key].validate(value)
            for key, value in kwargs.items()
        }
        return self._copy(_filter_kwargs=kwargs)

    def order_by(self, order_by: str) -> "MockDataSource":
        return self._copy(_order_by=order_by)

    def offset(self, offset: int) -> "MockDataSource":
        return self._copy(_offset=offset)

    def limit(self, limit: int) -> "MockDataSource":
        return self._copy(_limit=limit)

    async def all(self) -> typing.List["MockDataItem"]:
        items = self._items
        if self._filter_kwargs is not None:
            for key, value in self._filter_kwargs.items():
                items = [item for item in items if item[key] == value]
        if self._order_by is not None:
            order_by = self._order_by.lstrip("-")
            reverse = self._order_by.startswith("-")
            items = sorted(items, key=lambda item: item[order_by], reverse=reverse,)
        if self._offset is not None:
            items = items[self._offset :]
        if self._limit is not None:
            items = items[: self._limit]
        return [MockDataItem(item=item, container=self._items) for item in items]

    async def get(self) -> typing.Optional["MockDataItem"]:
        items = await self.all()
        return items[0] if items else None

    async def count(self) -> int:
        items = await self.all()
        return len(items)

    async def create(self, **kwargs) -> "MockDataItem":
        for key, field in self.schema.fields.items():
            if key not in kwargs and field.has_default():
                kwargs[key] = field.get_default_value()
        self._items.insert(0, kwargs)
        return MockDataItem(item=kwargs, container=self._items)


class MockDataItem(DataItem):
    def __init__(self, item: dict, container: typing.List[dict]) -> None:
        self._item = item
        self._container = container
        for key, value in item.items():
            setattr(self, key, value)

    async def delete(self) -> None:
        self._container.remove(self._item)

    async def update(self, **kwargs) -> None:
        for key, value in kwargs.items():
            self._item[key] = value
            setattr(self, key, value)
