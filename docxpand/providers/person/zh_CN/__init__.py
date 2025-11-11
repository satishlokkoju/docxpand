from collections import OrderedDict
from faker import Faker
from faker.providers.person.zh_CN import Provider as PersonProvider


class Provider(PersonProvider):
    __use_weighting__ = True

    fake = Faker('zh_CN')

    def name(self) -> str:
        if self not in self.generator.providers:
            self.generator.add_provider(self)
        # return self.generator.parse(pattern)
        return fake.name()
