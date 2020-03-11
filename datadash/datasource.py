import datetime


class Datasource:
    def search(self, term: str) -> 'Datasource':
        return self

    def order_by(self, column: str, reverse: bool = False) -> 'Datasource':
        return self

    def offset(self, offset: int) -> 'Datasource':
        return self

    def limit(self, limit: int) -> 'Datasource':
        return self

    async def all(self):
        return [
            {'username': 'tom@tomchristie.com', 'is_admin': True, 'joined': datetime.datetime.now()}
            for i in range(10)
        ]

    async def count(self) -> int:
        return 123
